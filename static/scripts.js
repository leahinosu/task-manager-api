function copyToClipboard(id) {
    text = document.getElementById(id).innerHTML;
    navigator.clipboard.writeText(text);
    alert("Copied!");
}