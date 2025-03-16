document.getElementById("screen-button").addEventListener("click", async () => {
    const skillsInput = document.getElementById("skills-input").value;
    const files = document.getElementById("resume-upload").files;

    if (!skillsInput || files.length === 0) {
        alert("Please enter skills and upload at least one resume.");
        return;
    }

    const formData = new FormData();
    formData.append("skills", skillsInput);
    for (let file of files) {
        formData.append("resumes", file);
    }

    try {
        const response = await fetch("/screen-resumes", {
            method: "POST",
            body: formData,
        });
        const results = await response.json();

        const resultsDiv = document.getElementById("results");
        resultsDiv.innerHTML = results.map(result => `
            <div class="result-item">
                <strong>${result.resume}</strong>: ${result.score}%<br>
                ${result.details}
            </div>
        `).join("");
    } catch (error) {
        console.error("Error:", error);
        alert("An error occurred while processing the resumes.");
    }
});