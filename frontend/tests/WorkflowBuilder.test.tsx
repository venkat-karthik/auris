import React from "react";
import { render, screen } from "@testing-library/react";
import WorkflowBuilder from "../src/components/WorkflowBuilder";

// Mock the Auth provider
jest.mock("../src/components/Providers", () => ({
  useAuth: () => ({
    token: "mock-token",
  }),
}));

// Mock react-flow-renderer to avoid canvas rendering errors in Jest environment
jest.mock("react-flow-renderer", () => {
  const ActualReactFlow = ({ children }: { children: React.ReactNode }) => (
    <div data-testid="react-flow">{children}</div>
  );
  return {
    __esModule: true,
    default: ActualReactFlow,
    Background: () => <div data-testid="rf-bg" />,
    Controls: () => <div data-testid="rf-controls" />,
    MiniMap: () => <div data-testid="rf-minimap" />,
    addEdge: jest.fn(),
    useEdgesState: () => [[], jest.fn(), jest.fn()],
    useNodesState: () => [[], jest.fn(), jest.fn()],
  };
});

describe("WorkflowBuilder Component", () => {
  it("renders the canvas and sidebar palette", () => {
    render(<WorkflowBuilder />);
    
    // Check palette options
    expect(screen.getByText("Auris Canvas")).toBeInTheDocument();
    expect(screen.getByText("Select Agent")).toBeInTheDocument();
    expect(screen.getByText("Add Flow Elements")).toBeInTheDocument();
    
    // Check React Flow canvas
    expect(screen.getByTestId("react-flow")).toBeInTheDocument();
  });
});
