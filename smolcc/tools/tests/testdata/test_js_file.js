// This is a test JavaScript file for GREP and GLOB tools

function sayHello() {
  console.log('Hello, world!');
}

function calculateSum(a, b) {
  return a + b;
}

// A sample class for testing
class Person {
  constructor(name, age) {
    this.name = name;
    this.age = age;
  }

  greet() {
    return `Hello, my name is ${this.name} and I'm ${this.age} years old.`;
  }
}

const config = {
  appName: 'TestApp',
  version: '1.0.0',
  features: ['search', 'filter', 'sort'],
  settings: {
    theme: 'dark',
    language: 'en',
    notifications: true
  }
};

// Export the functions and classes
module.exports = {
  sayHello,
  calculateSum,
  Person,
  config
};