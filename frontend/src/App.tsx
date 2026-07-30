import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import HomePage from "@/features/explorer/HomePage";
import JobPage from "@/features/job/JobPage";
import { queryClient } from "@/store/queryClient";

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/jobs/:jobId" element={<Navigate to="report" replace />} />
          <Route path="/jobs/:jobId/:tab" element={<JobPage />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
