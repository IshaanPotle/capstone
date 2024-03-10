const { Configuration, OpenAIApi } = require("@openai/api");

const config = new Configuration({
    apiKey: "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",
});

const openai = new OpenAIApi(config);

const runPrompt = async () => {
    const prompt = `
        write me a joke about a cat and a bowl of pasta. Return response in the following parsable JSON format:

        {
            "Q": "question",
            "A": "answer"
        }

    `;

    const response = await openai.createCompletion({
        model: "text-davinci-003",
        prompt: prompt,
        maxTokens: 2048, // Changed max_tokens to maxTokens
        temperature: 1,
    });

    const parsableJSONresponse = response.data.choices[0].text;
    const parsedResponse = JSON.parse(parsableJSONresponse);

    console.log("Question: ", parsedResponse.Q);
    console.log("Answer: ", parsedResponse.A);
};

runPrompt();
