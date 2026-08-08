import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";

const API_URL = "http://127.0.0.1:8000";

function DocumentHistory() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadDocuments = async () => {
    try {
      setLoading(true);

      const response = await axios.get(
        `${API_URL}/documents`
      );

      setDocuments(response.data);
      setError("");
    } catch (err) {
      console.error(err);

      setError(
        "Could not load document history."
      );
    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    loadDocuments();
  }, []);


  const handleDelete = async (id) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this document?"
    );

    if (!confirmed) {
      return;
    }

    try {
      await axios.delete(
        `${API_URL}/documents/${id}`
      );

      await loadDocuments();

    } catch (err) {
      console.error(err);

      alert(
        "Could not delete the document."
      );
    }
  };


  const handleReprocess = async (id) => {
    try {
      await axios.post(
        `${API_URL}/documents/${id}/reprocess`
      );

      await loadDocuments();

      alert(
        "Document has been queued for reprocessing."
      );

    } catch (err) {
      console.error(err);

      alert(
        err.response?.data?.detail ||
        "Could not reprocess the document."
      );
    }
  };


  const formatDate = (date) => {
    if (!date) {
      return "—";
    }

    return new Date(date).toLocaleDateString(
      "en-GB",
      {
        day: "2-digit",
        month: "short",
        year: "numeric"
      }
    );
  };


  const getStatusClass = (status) => {
    if (status === "completed") {
      return "history-status completed";
    }

    if (status === "failed") {
      return "history-status failed";
    }

    return "history-status processing";
  };


  if (loading) {
    return (
      <div className="page-heading">
        <div>
          <h2>Document History</h2>
          <p>Loading uploaded documents...</p>
        </div>
      </div>
    );
  }


  return (
    <div>

      {/* PAGE HEADER */}

      <div className="page-heading">

        <div>
          <h2>Document History</h2>

          <p>
            View previously processed procurement
            documents and extracted information.
          </p>
        </div>

      </div>


      {/* ERROR */}

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}


      {/* HISTORY TABLE */}

      <section className="card history-card">

        <div className="card-header">

          <div>
            <h3>Uploaded Documents</h3>

            <p>
              Complete history of document processing.
            </p>
          </div>

        </div>


        {documents.length === 0 ? (

          <div className="empty-state">
            No documents have been uploaded yet.
          </div>

        ) : (

          <div className="history-table-wrapper">

            <table className="history-table">

              <thead>

                <tr>
                  <th>Date</th>
                  <th>Document</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>OCR</th>
                  <th>AI Extraction</th>
                  <th>Request ID</th>
                  <th>Action</th>
                </tr>

              </thead>


              <tbody>

                {documents.map((document) => (

                  <tr key={document.id}>

                    <td>
                      {formatDate(
                        document.created_at
                      )}
                    </td>


                    <td>
                      <strong>
                        {document.filename}
                      </strong>
                    </td>


                    <td>
                      Invoice
                    </td>


                    <td>

                      <span
                        className={getStatusClass(
                          document.status
                        )}
                      >
                        {document.status
                          .charAt(0)
                          .toUpperCase() +
                          document.status.slice(1)}
                      </span>

                    </td>


                    <td>

                      {document.ocr_status ===
                      "completed"
                        ? "✓"
                        : "✗"}

                    </td>


                    <td>

                      {document.gemini_status ===
                      "completed"
                        ? "✓"
                        : "✗"}

                    </td>


                    <td>

                      {document.request_id
                        ? `#${document.request_id}`
                        : "—"}

                    </td>


                    <td>

                      <Link
                        to={`/documents/${document.id}`}
                        className="history-view-link"
                        >
                        View
                        </Link>

                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

          </div>

        )}

      </section>

    </div>
  );
}

export default DocumentHistory;