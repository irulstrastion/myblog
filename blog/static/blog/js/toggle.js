function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    // Animasi transisi tema
    html.style.transition = 'all 0.5s ease';
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Reset transition setelah animasi selesai
    setTimeout(() => {
        html.style.transition = '';
    }, 500);
}

// Load saved theme or default to dark
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Inisialisasi particles
    if (typeof particlesJS !== 'undefined') {
        particlesJS.load('particles-js', '{% static "blog/js/particles-config.json" %}');
    }
});