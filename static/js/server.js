//const express = require('express');
//const path = require('path');
//const app = express();

// Serve static files from the root directory
//app.use(express.static(path.join(__dirname, '..')));

// Start the server
//const PORT = process.env.PORT || 3000;
//app.listen(PORT, () => {
//    console.log(`Server is running on port ${PORT}`);
//});
const express = require('express');
const { resolve } = require('path'); // Import resolve from path module

// Define an async function to fetch the 'node-fetch' module
async function fetchData() {
  // Import 'node-fetch' module dynamically
  const fetch = await import('node-fetch');
  return fetch;
}

// Define your server logic inside an async function
async function startServer() {
  // Call the fetchData function to get the fetch function
  const fetch = await fetchData();

  // Create an Express app
  const app = express();
  const PORT = process.env.PORT || 3000;

  // Middleware to parse JSON bodies
  app.use(express.json());

  // Define route to serve static files from 'html' folder
  app.use(express.static('html'));
  

  // Define route to handle POST requests to '/cohere'
  app.post('/cohere', async (req, res) => {
    try {
      // Use the fetch function to make an HTTP request to the Cohere API
      const response = await fetch('https://api.cohere.ai/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer WrwwKEMSMjFySzaPxE9NmECZ6gjs4cINUtioGtNF'
        },
        body: JSON.stringify(req.body)
      });

      // Parse the response as JSON
      const data = await response.json();

      // Send the response data back to the client
      res.json(data);
    } catch (error) {
      // Handle errors
      console.error('Error:', error);
      res.status(500).json({ error: 'Internal Server Error' });
    }
  });

  // Define route to serve user1.html from 'html' folder
  app.get('/user1.html', (req, res) => {
    // Use resolve to get absolute path of user1.html inside 'html' folder
    const filePath = resolve('..', 'html', 'user1.html');
    res.sendFile(filePath);
  });

  // Start the server
  app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
  });
}

// Call the async function to start the server
startServer().catch(error => {
  console.error('Error starting server:', error);
});


