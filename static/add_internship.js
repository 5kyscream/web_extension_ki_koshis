document.getElementById('internshipForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());
    
    try {
        const response = await fetch('/add_internship', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('Internship posted successfully!');
            this.reset();
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        alert('Error posting internship: ' + error.message);
    }
});