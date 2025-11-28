const API_BASE_URL = '/api'; // All requests will be proxied by Firebase Hosting

/**
 * Fetches all conversations from the backend.
 * NOTE: With Firestore, this would typically be handled by the Firebase SDK on the client.
 * This is a placeholder and may not be the most efficient way.
 */
export const getConversations = async () => {
  // This function will need to be re-implemented using the Firebase Client SDK
  // to list conversations from Firestore, ideally with authentication.
  console.warn("getConversations is not implemented for Firestore yet.");
  return []; // Returning empty for now.
};

/**
 * Creates a new conversation.
 * In our new model, a conversation is implicitly created by the first message.
 */
export const createConversation = async () => {
    // We generate a unique ID on the client-side. This could also be done on the backend.
    const id = `conv_${new Date().getTime()}_${Math.random().toString(36).substring(2, 9)}`;
    return { id };
};


/**
 * Sends a message to a specific conversation and gets the LLM council'''s response.
 * @param {string} id - The conversation ID.
 * @param {string} prompt - The user'''s message.
 * @returns {Promise<object>} - The assistant'''s response object with all stages and metadata.
 */
export const sendMessage = async (id, prompt) => {
  const response = await fetch(`${API_BASE_URL}/conversations/${id}/message`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ prompt }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to send message: ${errorText}`);
  }

  return response.json();
};

/**
 * Fetches messages for a specific conversation.
 * NOTE: This should also be replaced with the Firebase Client SDK for real-time updates.
 */
export const getMessages = async (id) => {
  console.warn("getMessages is not implemented for Firestore yet.");
  return []; // Returning empty for now.
};
