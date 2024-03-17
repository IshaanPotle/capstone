<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Search Results</title>
    
    <style>
        /* Styling for the box */
        #generatedText {
            border: 1px solid #ffffff; /* Add a border */
            padding: 20px; /* Add padding inside the box */
            margin-top: 20px; /* Add margin to create some space */
            width: 80%; /* Set the width of the box */
            max-width: 600px; /* Set maximum width to prevent the box from becoming too wide */
            word-wrap: break-word; /* Ensure long text wraps within the box */
            min-height: 100px; /* Set a minimum height for the box */
            overflow: auto; /* Add scrollbars if content overflows */
            background-color: white; /* Set the background color to white */
        }
    </style>
</head>
<body>
    <h1>Results for "<span id="keyword"></span>"</h1>
    <div id="generatedText">
        <h1>Hello</h1>
    </div>
    <script>
        function generateText(keyword) {
            const source = new EventSource('/generate', { withCredentials: true });
            source.onmessage = function(event) {
                // Parse the received data
                const data = JSON.parse(event.data);
                // Manipulate the HTML content based on the received data
                const htmlContent = `
                    <h2>${data.title}</h2>
                    <p>${data.description}</p>
                    <a href="${data.link}" target="_blank">Read more</a>
                `;
                // Set the innerHTML of the #generatedText element
                document.getElementById('generatedText').innerHTML = htmlContent;
            };
            source.onerror = function(error) {
                console.error('Error fetching data:', error);
            };
        }
        const keyword = 'pythagoras theorem'; // Replace with your keyword
        document.getElementById('keyword').innerText = keyword;
        generateText(keyword);
    </script>
</body>
</html>
