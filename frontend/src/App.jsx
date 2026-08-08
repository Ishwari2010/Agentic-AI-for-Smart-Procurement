import { BrowserRouter, Routes, Route } from "react-router-dom";

import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import DocumentIntelligence from "./pages/DocumentIntelligence";
import DocumentHistory from "./pages/DocumentHistory";
import DocumentDetails from "./pages/DocumentDetails";

function Placeholder({ title }) {
  return (
    <div className="page">
      <div className="page-heading">
        <div>
          <h2>{title}</h2>
          <p>This module will be implemented next.</p>
        </div>
      </div>

      <section className="card placeholder-card">
        <h3>{title}</h3>
        <p>Coming soon.</p>
      </section>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />

        <div className="main-area">
          <Header />

          <main>
            <Routes>
              <Route
                path="/"
                element={<Placeholder title="Dashboard" />}
              />

              <Route
                path="/documents"
                element={<DocumentIntelligence />}
              />


              <Route
                path="/documents"
                element={<DocumentIntelligence />}
              />

              <Route
                path="/documents/history"
                element={<DocumentHistory />}
              />

              <Route
                path="/documents/:processingId"
                element={<DocumentDetails />}
              />

              <Route
                path="/requests"
                element={<Placeholder title="Requests" />}
              />

              <Route
                path="/contracts"
                element={<Placeholder title="Contracts" />}
              />

              <Route
                path="/inventory"
                element={<Placeholder title="Inventory" />}
              />

              <Route
                path="/emails"
                element={<Placeholder title="Emails" />}
              />

              <Route
                path="/operations"
                element={<Placeholder title="Operations" />}
              />

              <Route
                path="/logs"
                element={<Placeholder title="Logs" />}
              />

              <Route
                path="/users"
                element={<Placeholder title="Users" />}
            
              />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;