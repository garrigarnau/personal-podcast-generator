import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authService } from '../services/auth';
import { UserPlus, AlertCircle, CheckCircle2 } from 'lucide-react';

const Signup: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [error, setError] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    // Validate password length
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    // Validate password max length (bcrypt limit)
    if (formData.password.length > 72) {
      setError('Password cannot be longer than 72 characters');
      return;
    }

    setLoading(true);

    try {
      await authService.signup({
        username: formData.username,
        email: formData.email,
        password: formData.password,
      });
      navigate('/'); // Redirect to home after successful signup
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
        'Signup failed. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const passwordStrength = (password: string): string => {
    if (password.length === 0) return '';
    if (password.length < 8) return 'weak';
    if (password.length < 12) return 'medium';
    return 'strong';
  };

  const strength = passwordStrength(formData.password);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50 px-4 py-12">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-100 rounded-full mb-4">
            <UserPlus className="w-8 h-8 text-purple-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Create Account</h1>
          <p className="text-gray-600 mt-2">Start generating personalized podcasts</p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Signup Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label
              htmlFor="username"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Username
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              minLength={3}
              maxLength={50}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
              placeholder="Choose a username"
            />
          </div>

          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Email Address
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
              placeholder="your@email.com"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Password
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              minLength={8}
              maxLength={72}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
              placeholder="8-72 characters"
            />
            {formData.password && (
              <div className="mt-2">
                <div className="flex gap-1">
                  <div
                    className={`h-1 flex-1 rounded ${
                      strength === 'weak' ? 'bg-red-500' :
                      strength === 'medium' ? 'bg-yellow-500' :
                      strength === 'strong' ? 'bg-green-500' :
                      'bg-gray-200'
                    }`}
                  />
                  <div
                    className={`h-1 flex-1 rounded ${
                      strength === 'medium' || strength === 'strong' ? 'bg-yellow-500' :
                      strength === 'strong' ? 'bg-green-500' :
                      'bg-gray-200'
                    }`}
                  />
                  <div
                    className={`h-1 flex-1 rounded ${
                      strength === 'strong' ? 'bg-green-500' : 'bg-gray-200'
                    }`}
                  />
                </div>
                <p className={`text-xs mt-1 ${
                  strength === 'weak' ? 'text-red-600' :
                  strength === 'medium' ? 'text-yellow-600' :
                  'text-green-600'
                }`}>
                  {strength === 'weak' && 'Weak password'}
                  {strength === 'medium' && 'Medium strength'}
                  {strength === 'strong' && 'Strong password'}
                </p>
              </div>
            )}
          </div>

          <div>
            <label
              htmlFor="confirmPassword"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Confirm Password
            </label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              maxLength={72}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
              placeholder="Confirm your password"
            />
            {formData.confirmPassword && (
              <div className="mt-2 flex items-center gap-2">
                {formData.password === formData.confirmPassword ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-green-600" />
                    <p className="text-xs text-green-600">Passwords match</p>
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-4 h-4 text-red-600" />
                    <p className="text-xs text-red-600">Passwords don't match</p>
                  </>
                )}
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 rounded-lg font-semibold hover:from-purple-700 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Creating account...
              </span>
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        {/* Login Link */}
        <div className="mt-6 text-center">
          <p className="text-gray-600">
            Already have an account?{' '}
            <Link
              to="/login"
              className="text-purple-600 font-semibold hover:text-purple-700 transition"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Signup;
