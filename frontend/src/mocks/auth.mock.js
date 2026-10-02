import { ApiError } from "../services/apiClient";
import { delay } from "./delay";
import usersData from "./data/users.json";

const users = usersData.map((user) => ({ ...user }));
const mockPasswords = new Map([["john@example.com", "password"]]);

export async function register({ name, email, password }) {
  await delay();
  if (!name || !email || !password) {
    throw new ApiError("Validation error", { status: 422, data: null });
  }
  if (users.some((user) => user.email === email)) {
    throw new ApiError("Email already registered", { status: 409, data: null });
  }
  const user = { id: `user_${Date.now()}`, name, email };
  users.push(user);
  mockPasswords.set(email, password);
  return { user };
}

export async function login({ email, password }) {
  await delay();
  if (!email || !password) {
    throw new ApiError("Validation error", { status: 422, data: null });
  }
  const user = users.find((item) => item.email === email);
  if (!user || mockPasswords.get(email) !== password) {
    throw new ApiError("Invalid email or password", { status: 401, data: null });
  }
  return {
    access_token: `mock_token_${user.id}`,
    token_type: "bearer",
    user,
  };
}

export async function getCurrentUser() {
  await delay(150);
  const token = window.localStorage.getItem("marketingos_access_token");
  if (!token) {
    throw new ApiError("Authentication required", { status: 401, data: null });
  }
  const userId = token.replace("mock_token_", "");
  const user = users.find((item) => item.id === userId) ?? users[0];
  return { id: user.id, name: user.name, email: user.email };
}

export async function changePassword({ currentPassword, newPassword }) {
  await delay();
  const token = window.localStorage.getItem("marketingos_access_token");
  const userId = token?.replace("mock_token_", "");
  const user = users.find((item) => item.id === userId);
  if (!user) throw new ApiError("Authentication required", { status: 401, data: null });
  if (mockPasswords.get(user.email) !== currentPassword) throw new ApiError("Current password is incorrect.", { status: 401, data: null });
  if (!newPassword || newPassword.length < 6) throw new ApiError("New password must be at least 6 characters.", { status: 422, data: null });
  mockPasswords.set(user.email, newPassword);
  return { message: "Password changed in demo mode." };
}

export async function logout() {
  await delay(80);
  return null;
}
