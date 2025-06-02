// This is a test TypeScript file for GREP and GLOB tools

interface User {
  id: number;
  name: string;
  email: string;
  active: boolean;
}

type UserRole = 'admin' | 'editor' | 'viewer';

function createUser(name: string, email: string): User {
  return {
    id: Math.floor(Math.random() * 1000),
    name,
    email,
    active: true
  };
}

class UserManager {
  private users: User[] = [];

  constructor() {
    this.users = [];
  }

  addUser(user: User): void {
    this.users.push(user);
  }

  findUserById(id: number): User | undefined {
    return this.users.find(user => user.id === id);
  }

  getAllUsers(): User[] {
    return [...this.users];
  }
}

export const DEFAULT_USER: User = {
  id: 0,
  name: 'Guest',
  email: 'guest@example.com',
  active: false
};

export { User, UserRole, createUser, UserManager };