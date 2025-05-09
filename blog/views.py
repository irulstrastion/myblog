# blog/views.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import Article
from .forms import CommentForm
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO, StringIO
import base64
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import sys
import contextlib
import numpy as np

# Fungsi-fungsi blog tetap sama
def home(request):
    articles = Article.objects.order_by('-created_at')
    return render(request, 'blog/home.html', {'articles': articles})

def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug)
    comments = article.comments.order_by('-created_at')

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.save()
            return redirect(article.get_absolute_url())
    else:
        form = CommentForm()

    return render(request, 'blog/detail.html', {
        'article': article,
        'comments': comments,
        'form': form
    })

def about(request):
    return render(request, 'blog/about.html')

# Fungsi eksplorasi data yang diperbaiki
def explore(request):
    context = {
        'stats_html': None,
        'plot_base64': None,
        'error_message': None,
        'console_output': "",
        'user_code': request.POST.get('user_code', ''),
        'columns': None,
        'df_sample': None
    }

    if request.method == 'POST':
        # Handle file upload
        if 'datafile' in request.FILES:
            try:
                datafile = request.FILES['datafile']
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
                filename = fs.save(datafile.name, datafile)
                filepath = fs.path(filename)

                if filename.endswith('.csv'):
                    df = pd.read_csv(filepath)
                elif filename.endswith(('.xls', '.xlsx')):
                    df = pd.read_excel(filepath)
                else:
                    raise ValueError("Format file tidak didukung")

                # Clean and process data
                df = clean_dataframe(df)
                
                # Store in session
                request.session['uploaded_file_path'] = filepath
                request.session['df_columns'] = list(df.columns)
                request.session['df_sample'] = df.head(5).to_html(classes='table table-bordered')

                # Generate stats and plot
                context.update(generate_analysis(df))

            except Exception as e:
                context['error_message'] = f"Error: {str(e)}"

        # Handle code execution
        elif 'user_code' in request.POST:
            try:
                filepath = request.session.get('uploaded_file_path')
                if filepath and os.path.exists(filepath):
                    if filepath.endswith('.csv'):
                        df = pd.read_csv(filepath)
                    elif filepath.endswith(('.xls', '.xlsx')):
                        df = pd.read_excel(filepath)
                    df = clean_dataframe(df)
                else:
                    df = None

                # Prepare execution environment
                local_vars = {
                    'pd': pd,
                    'df': df,
                    'plt': plt,
                    'sns': sns,
                    'np': np
                }

                # Capture output
                output = StringIO()
                sys.stdout = output
                
                # Execute code
                exec(context['user_code'], {'__builtins__': None}, local_vars)
                
                # Check for plots
                if len(plt.get_fignums()) > 0:
                    buf = BytesIO()
                    plt.savefig(buf, format='png', bbox_inches='tight')
                    plt.close()
                    context['plot_base64'] = base64.b64encode(buf.getvalue()).decode('utf-8')
                
                context['console_output'] = output.getvalue()

            except Exception as e:
                context['error_message'] = f"Error executing code: {str(e)}"
            finally:
                sys.stdout = sys.__stdout__
                plt.close('all')

    # Add session data to context
    context['columns'] = request.session.get('df_columns', [])
    context['df_sample'] = request.session.get('df_sample')
    
    return render(request, 'blog/explore.html', context)

def clean_dataframe(df):
    """Helper function to clean dataframe"""
    # Convert numeric columns with thousand separators
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = pd.to_numeric(df[col].astype(str).str.replace('[^\d.]', '', regex=True), errors='ignore')
    return df

def generate_analysis(df):
    """Generate stats and plots from dataframe"""
    result = {}
    
    # Descriptive stats
    numeric_df = df.select_dtypes(include='number')
    if not numeric_df.empty:
        result['stats_html'] = numeric_df.describe().to_html(classes='table table-bordered')
        
        # Correlation heatmap
        plt.figure(figsize=(10, 6))
        sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm', center=0)
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()
        result['plot_base64'] = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return result