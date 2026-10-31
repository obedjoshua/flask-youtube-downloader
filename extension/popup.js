document.addEventListener('DOMContentLoaded', async () => {
    const urlInput = document.getElementById('page-url');
    const dlBtn = document.getElementById('dl-btn');
    const status = document.getElementById('status');

    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab && tab.url) {
        urlInput.value = tab.url;
    }

    dlBtn.addEventListener('click', async () => {
        const url = urlInput.value;
        const mode = document.getElementById('mode').value;
        const embedCC = document.getElementById('embed-cc').checked;
        const ccLang = document.getElementById('cc-lang').value;

        if (!url) {
            status.innerText = 'No URL detected.';
            return;
        }

        status.innerText = 'Sending task to Flask server...';
        dlBtn.disabled = true;

        let endpoint = 'http://127.0.0.1:5000/download-universal';
        let payload = { 
            url, 
            media_type: mode === 'universal_audio' ? 'audio_only' : 'video',
            embed_cc: embedCC,
            cc_lang: ccLang
        };

        if (mode === 'music') {
            endpoint = 'http://127.0.0.1:5000/download-music';
            payload = { url, format: 'mp3', quality: '320' };
        }

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error);

            status.innerText = 'Download finished on server!';
        } catch (err) {
            status.innerText = 'Error: ' + err.message;
        } finally {
            dlBtn.disabled = false;
        }
    });
});