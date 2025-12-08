import { useAuth } from '@clerk/clerk-react';
import { db } from './firebase';
import { collection, query, where, orderBy, getDocs, doc, onSnapshot } from 'firebase/firestore';

const API_BASE_URL = '/api'; // All requests will be proxied by Firebase Hosting

/**
 * Custom hook that provides authenticated API methods
 */
export function useApi() {
  const { getToken, userId } = useAuth();

  /**
   * Fetches all conversations for the current user from Firestore
   */
  const getConversations = async () => {
    if (!userId) {
      return [];
    }

    try {
      const conversationsRef = collection(db, 'conversations');
      const q = query(
        conversationsRef,
        where('userId', '==', userId),
        orderBy('createdAt', 'desc')
      );

      const querySnapshot = await getDocs(q);
      return querySnapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data(),
        created_at: doc.data().createdAt?.toDate?.()?.toISOString() || new Date().toISOString()
      }));
    } catch (error) {
      console.error('Error fetching conversations:', error);
      return [];
    }
  };

  /**
   * Creates a new conversation
   */
  const createConversation = async () => {
    // Generate a unique ID on the client-side
    const id = `conv_${new Date().getTime()}_${Math.random().toString(36).substring(2, 9)}`;
    return { id };
  };

  /**
   * Sends a message to a specific conversation and gets the LLM council's response
   * @param {string} id - The conversation ID
   * @param {string} prompt - The user's message
   * @returns {Promise<object>} - The assistant's response object with all stages and metadata
   */
  const sendMessage = async (id, prompt) => {
    const token = await getToken();

    const response = await fetch(`${API_BASE_URL}/conversations/${id}/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
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
   * Fetches messages for a specific conversation from Firestore
   * @param {string} id - The conversation ID
   * @returns {Promise<Array>} - Array of messages
   */
  const getMessages = async (id) => {
    if (!userId) {
      return [];
    }

    try {
      const messagesRef = collection(db, 'conversations', id, 'messages');
      const q = query(messagesRef, orderBy('createdAt', 'asc'));

      const querySnapshot = await getDocs(q);
      return querySnapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
    } catch (error) {
      console.error('Error fetching messages:', error);
      return [];
    }
  };

  /**
   * Subscribes to real-time updates for messages in a conversation
   * @param {string} id - The conversation ID
   * @param {Function} callback - Callback function to receive updates
   * @returns {Function} - Unsubscribe function
   */
  const subscribeToMessages = (id, callback) => {
    if (!userId) {
      return () => {};
    }

    const messagesRef = collection(db, 'conversations', id, 'messages');
    const q = query(messagesRef, orderBy('createdAt', 'asc'));

    return onSnapshot(q, (querySnapshot) => {
      const messages = querySnapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
      callback(messages);
    });
  };

  return {
    getConversations,
    createConversation,
    sendMessage,
    getMessages,
    subscribeToMessages
  };
}

// Export legacy functions for backward compatibility (will need to be updated in components)
export const getConversations = async () => {
  console.warn("getConversations called without authentication context. Use useApi() hook instead.");
  return [];
};

export const createConversation = async () => {
  const id = `conv_${new Date().getTime()}_${Math.random().toString(36).substring(2, 9)}`;
  return { id };
};

export const sendMessage = async (id, prompt) => {
  console.warn("sendMessage called without authentication context. Use useApi() hook instead.");
  throw new Error("Authentication required. Use useApi() hook instead.");
};

export const getMessages = async (id) => {
  console.warn("getMessages called without authentication context. Use useApi() hook instead.");
  return [];
};
