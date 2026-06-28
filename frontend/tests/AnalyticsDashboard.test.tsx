/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import DashboardPage from "../src/app/dashboard/page";

// Mock the Auth provider
jest.mock("../src/components/Providers", () => ({
  useAuth: () => ({
    token: "mock-token",
    orgId: 1,
  }),
}));

// Mock DashboardLayout to avoid full page layout rendering overhead
jest.mock("../src/components/DashboardLayout", () => {
  return function MockLayout({ children }: { children: React.ReactNode }) {
    return <div data-testid="dashboard-layout">{children}</div>;
  };
});

// Mock Recharts
jest.mock("recharts", () => {
  const OriginalModule = jest.requireActual("recharts");
  return {
    ...OriginalModule,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  };
});

describe("Dashboard Analytics Page", () => {
  beforeEach(() => {
    // Mock global fetch
    global.fetch = jest.fn((url: string) => {
      if (url.includes("/billing/balance")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ balance_credits: 500 }),
        });
      }
      if (url.includes("/agents")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([{ id: 1, name: "Support Agent" }]),
        });
      }
      if (url.includes("/calls")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([]),
        });
      }
      if (url.includes("/analytics/agents")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([]),
        });
      }
      if (url.includes("/analytics/call_outcomes")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([]),
        });
      }
      return Promise.reject(new Error("Unknown route"));
    }) as any;
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it("renders the dashboard page structure and metrics cards after fetching data", async () => {
    render(<DashboardPage />);
    
    // Initially showing loader
    expect(screen.getByRole("status") || screen.getByText(/loading/i) || screen.getByTestId("dashboard-layout")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Overview")).toBeInTheDocument();
      expect(screen.getByText("Credit Balance")).toBeInTheDocument();
      expect(screen.getByText("Active Agents")).toBeInTheDocument();
      expect(screen.getByText("Calls Handled")).toBeInTheDocument();
    });
  });
});
