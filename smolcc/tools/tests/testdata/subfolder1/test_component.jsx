// A sample React component for testing
import React, { useState, useEffect } from 'react';

// A simple functional component
function TestComponent({ name, age }) {
  const [count, setCount] = useState(0);
  
  useEffect(() => {
    console.log('Component mounted');
    return () => {
      console.log('Component unmounted');
    };
  }, []);

  const handleClick = () => {
    setCount(count + 1);
  };

  return (
    <div className="test-component">
      <h1>Hello, {name}!</h1>
      <p>Age: {age}</p>
      <p>Count: {count}</p>
      <button onClick={handleClick}>Increment</button>
    </div>
  );
}

// A class component for comparison
class ClassComponent extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      count: 0
    };
  }

  componentDidMount() {
    console.log('Class component mounted');
  }

  componentWillUnmount() {
    console.log('Class component unmounted');
  }

  handleClick = () => {
    this.setState({ count: this.state.count + 1 });
  };

  render() {
    return (
      <div className="class-component">
        <h1>Class Component</h1>
        <p>Count: {this.state.count}</p>
        <button onClick={this.handleClick}>Increment</button>
      </div>
    );
  }
}

export { TestComponent, ClassComponent };