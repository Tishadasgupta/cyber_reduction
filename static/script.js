async function processText() {
    const text = document.getElementById('inputText').value;
    const mode = document.getElementById('mode').value;
    const outputBox = document.getElementById('outputText');
    const scoreVal = document.getElementById('scoreVal');
    const tableBody = document.getElementById('entityTableBody');

    if (!text.trim()) { alert("Please enter text!"); return; }

    outputBox.value = "Processing...";
    
    try {
        const response = await fetch('/api/redact', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text, mode: mode })
        });
        const data = await response.json();

        outputBox.value = data.redacted;
        scoreVal.innerText = data.score + "%";

        tableBody.innerHTML = "";
        data.entities.forEach(ent => {
            let row = `<tr>
                <td style="color: #ff5555">${ent['Entity Name']}</td>
                <td>${ent['Extracted Text']}</td>
                <td>${ent['Start Index']}</td>
                <td>${ent['End Index']}</td>
            </tr>`;
            tableBody.innerHTML += row;
        });

    } catch (error) {
        console.error("Error:", error);
        outputBox.value = "Server Error.";
    }
}