/**
 * Authentication service for managing user login, signup, and tokens.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface SignupData {
  username: string;
  email: string;
  password: string;
}

export interface LoginData {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  username: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  created_at: string;
}

/**
 * Auth service class for handling authentication operations.
 */
class AuthService {
  private readonly TOKEN_KEY = 'auth_token';
  private readonly USER_KEY = 'auth_user';

  /**
   * Sign up a new user.
   */
  async signup(data: SignupData): Promise<AuthResponse> {
    const response = await axios.post<AuthResponse>(
      `${API_BASE_URL}/api/v1/auth/signup`,
      data
    );

    // Store token and user info
    this.setToken(response.data.access_token);
    this.setUser({
      id: response.data.user_id,
      username: response.data.username,
    });

    return response.data;
  }

  /**
   * Login an existing user.
   */
  async login(data: LoginData): Promise<AuthResponse> {
    const response = await axios.post<AuthResponse>(
      `${API_BASE_URL}/api/v1/auth/login`,
      data
    );

    // Store token and user info
    this.setToken(response.data.access_token);
    this.setUser({
      id: response.data.user_id,
      username: response.data.username,
    });

    return response.data;
  }

  /**
   * Get current user information from the API.
   */
  async getCurrentUser(): Promise<User> {
    const token = this.getToken();

    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await axios.get<User>(
      `${API_BASE_URL}/api/v1/auth/me`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    return response.data;
  }

  /**
   * Logout the current user.
   */
  logout(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  }

  /**
   * Get stored authentication token.
   */
  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  /**
   * Set authentication token.
   */
  setToken(token: string): void {
    localStorage.setItem(this.TOKEN_KEY, token);
  }

  /**
   * Get stored user info.
   */
  getUser(): { id: string; username: string } | null {
    const userStr = localStorage.getItem(this.USER_KEY);
    return userStr ? JSON.parse(userStr) : null;
  }

  /**
   * Set user info.
   */
  setUser(user: { id: string; username: string }): void {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  }

  /**
   * Check if user is authenticated.
   */
  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  /**
   * Get authorization header for API requests.
   */
  getAuthHeader(): { Authorization: string } | {} {
    const token = this.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }
}

export const authService = new AuthService();
