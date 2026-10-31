(function () {
    if (document.getElementById('flask-downloader-quick-btn')) return;

    const btn = document.createElement('button');
    btn.id = 'flask-downloader-quick-btn';
    btn.innerText = '⚡ Download Media';
    
    Object.assign(btn.style, {
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        zIndex: '999999',
        padding: '10px 16px',
        backgroundColor: '#2563eb',
        color: '#ffffff',
        border: 'none',
        borderRadius: '50px',
        fontWeight: 'bold',
        fontSize: '13px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        cursor: 'pointer'
    });

    btn.addEventListener('click', async () => {
        btn.innerText = '⏳ Processing...';
        btn.disabled = true;

        try {
            const response = await fetch('http://127.0.0.1:5000/download-universal', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: window.location.href, media_type: 'video', embed_cc: true, cc_lang: 'en' })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error);

            btn.innerText = '✅ Downloaded!';
            setTimeout(() => {
                btn.innerText = '⚡ Download Media';
                btn.disabled = false;
            }, 3000);
        } catch (err) {
            alert('Download failed: ' + err.message);
            btn.innerText = '⚡ Download Media';
            btn.disabled = false;
        }
    });

    document.body.appendChild(btn);
})();