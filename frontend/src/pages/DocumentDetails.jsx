import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import axios from "axios";

const API_URL = "http://127.0.0.1:8000";

function DocumentDetails() {
  const { processingId } = useParams();
  const navigate = useNavigate();

  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState(false);


  // ============================================================
  // Load Document Details
  // ============================================================

  const loadDocument = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await axios.get(
        `${API_URL}/documents/${processingId}`
      );

      setDocument(response.data);

    } catch (err) {
      console.error(
        "Document loading error:",
        err
      );

      setError(
        err.response?.data?.detail ||
        "Could not load document details."
      );

    } finally {
      setLoading(false);
    }
  };


  // ============================================================
  // Initial Load
  // ============================================================

  useEffect(() => {
    loadDocument();
  }, [processingId]);


  // ============================================================
  // Reprocess Document
  // ============================================================

  const handleReprocess = async () => {
    const confirmed = window.confirm(
      "Are you sure you want to reprocess this document?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setActionLoading(true);
      setError("");

      await axios.post(
        `${API_URL}/documents/${processingId}/reprocess`
      );

      await loadDocument();

      alert(
        "Document has been queued for reprocessing."
      );

    } catch (err) {
      console.error(
        "Reprocess error:",
        err
      );

      setError(
        err.response?.data?.detail ||
        "Could not reprocess the document."
      );

    } finally {
      setActionLoading(false);
    }
  };


  // ============================================================
  // Delete Document
  // ============================================================

  const handleDelete = async () => {
    const confirmed = window.confirm(
      "Are you sure you want to permanently delete this document?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setActionLoading(true);
      setError("");

      await axios.delete(
        `${API_URL}/documents/${processingId}`
      );

      alert(
        "Document deleted successfully."
      );

      navigate("/documents/history");

    } catch (err) {
      console.error(
        "Delete error:",
        err
      );

      setError(
        err.response?.data?.detail ||
        "Could not delete the document."
      );

    } finally {
      setActionLoading(false);
    }
  };


  // ============================================================
  // Date Formatter
  // ============================================================

  const formatDate = (date) => {
    if (!date) {
      return "—";
    }

    return new Date(date).toLocaleString(
      "en-GB",
      {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      }
    );
  };


  // ============================================================
  // Status Helper
  // ============================================================

  const getStatusClass = (status) => {
    if (status === "completed") {
      return "history-status completed";
    }

    if (status === "failed") {
      return "history-status failed";
    }

    return "history-status processing";
  };


  // ============================================================
  // Loading
  // ============================================================

  if (loading) {
    return (
      <div className="page-heading">

        <div>
          <h2>
            Document Details
          </h2>

          <p>
            Loading document information...
          </p>
        </div>

      </div>
    );
  }


  // ============================================================
  // Error / Not Found
  // ============================================================

  if (error && !document) {
    return (
      <div>

        <div className="page-heading">

          <div>
            <h2>
              Document Details
            </h2>

            <p>
              Unable to load this document.
            </p>
          </div>

        </div>

        <div className="error-message">
          {error}
        </div>

        <button
          className="secondary-button"
          onClick={() =>
            navigate("/documents/history")
          }
        >
          Back to History
        </button>

      </div>
    );
  }


  if (!document) {
    return null;
  }


  // ============================================================
  // Render
  // ============================================================

  return (
    <div>

      {/* ======================================================
          PAGE HEADER
      ====================================================== */}

      <div className="page-heading">

        <div>

          <h2>
            Document Details
          </h2>

          <p>
            Complete processing information and
            extracted data.
          </p>

        </div>


        <div>

          <button
            className="secondary-button"
            onClick={() =>
              navigate("/documents/history")
            }
          >
            ← Back to History
          </button>

        </div>

      </div>


      {/* ======================================================
          DOCUMENT INFORMATION
      ====================================================== */}

      <section className="card">

        <div className="card-header">

          <div>

            <h3>
              {document.filename}
            </h3>

            <p>
              Procurement document
            </p>

          </div>


          <span
            className={getStatusClass(
              document.status
            )}
          >
            {document.status
              ? document.status
                  .charAt(0)
                  .toUpperCase() +
                document.status.slice(1)
              : "Unknown"}
          </span>

        </div>


        <div className="information-grid">

          <div>

            <span>
              Processing ID
            </span>

            <strong>
              #{document.id}
            </strong>

          </div>


          <div>

            <span>
              Request ID
            </span>

            <strong>
              {document.request_id
                ? `#${document.request_id}`
                : "—"}
            </strong>

          </div>


          <div>

            <span>
              Filename
            </span>

            <strong>
              {document.filename}
            </strong>

          </div>


          <div>

            <span>
              File Type
            </span>

            <strong>
              Invoice
            </strong>

          </div>


          <div>

            <span>
              Uploaded
            </span>

            <strong>
              {formatDate(
                document.created_at
              )}
            </strong>

          </div>


          <div>

            <span>
              Last Updated
            </span>

            <strong>
              {formatDate(
                document.updated_at
              )}
            </strong>

          </div>

        </div>

      </section>


      {/* ======================================================
          PROCESSING PIPELINE
      ====================================================== */}

      <section className="card">

        <div className="card-header">

          <div>

            <h3>
              Processing Pipeline
            </h3>

            <p>
              Status of each Document Intelligence
              processing stage.
            </p>

          </div>

        </div>


        <div className="pipeline">


          {/* Uploaded */}

          <div
            className={`pipeline-step ${
              document.id
                ? "completed"
                : ""
            }`}
          >

            <div className="step-circle">
              ✓
            </div>

            <div>

              <strong>
                Uploaded
              </strong>

              <span>
                Document received
              </span>

            </div>

          </div>


          <div className="pipeline-line"></div>


          {/* Kafka */}

          <div
            className={`pipeline-step ${
              document.status !== "queued"
                ? "completed"
                : ""
            }`}
          >

            <div className="step-circle">

              {document.status !== "queued"
                ? "✓"
                : "2"}

            </div>

            <div>

              <strong>
                Queued
              </strong>

              <span>
                Kafka invoice-topic
              </span>

            </div>

          </div>


          <div className="pipeline-line"></div>


          {/* OCR */}

          <div
            className={`pipeline-step ${
              document.ocr_status ===
              "completed"
                ? "completed"
                : ""
            }`}
          >

            <div className="step-circle">

              {document.ocr_status ===
              "completed"
                ? "✓"
                : "3"}

            </div>

            <div>

              <strong>
                OCR
              </strong>

              <span>
                Tesseract processing
              </span>

            </div>

          </div>


          <div className="pipeline-line"></div>


          {/* Gemini */}

          <div
            className={`pipeline-step ${
              document.gemini_status ===
              "completed"
                ? "completed"
                : ""
            }`}
          >

            <div className="step-circle">

              {document.gemini_status ===
              "completed"
                ? "✓"
                : "4"}

            </div>

            <div>

              <strong>
                AI Extraction
              </strong>

              <span>
                Gemini processing
              </span>

            </div>

          </div>


          <div className="pipeline-line"></div>


          {/* Database */}

          <div
            className={`pipeline-step ${
              document.status ===
              "completed"
                ? "completed"
                : ""
            }`}
          >

            <div className="step-circle">

              {document.status ===
              "completed"
                ? "✓"
                : "5"}

            </div>

            <div>

              <strong>
                Database
              </strong>

              <span>
                PostgreSQL
              </span>

            </div>

          </div>

        </div>

      </section>


      {/* ======================================================
          ERROR
      ====================================================== */}

      {error && (

        <div className="error-message">
          {error}
        </div>

      )}


      {/* ======================================================
          OCR TEXT
      ====================================================== */}

      <section className="card">

        <div className="card-header">

          <div>

            <h3>
              OCR Text
            </h3>

            <p>
              Text extracted from the invoice
              using Tesseract OCR.
            </p>

          </div>


          <span
            className={
              document.ocr_status ===
              "completed"
                ? "history-status completed"
                : "history-status processing"
            }
          >
            {document.ocr_status}
          </span>

        </div>


        <div className="ocr-result">

          {document.ocr_text
            ? document.ocr_text
            : document.ocr_status ===
              "pending"
            ? "OCR has not been completed yet."
            : "No OCR text available."}

        </div>

      </section>


      {/* ======================================================
          GEMINI STRUCTURED DATA
      ====================================================== */}

      <section className="card">

        <div className="card-header">

          <div>

            <h3>
              AI Extracted Information
            </h3>

            <p>
              Structured information extracted
              by Gemini.
            </p>

          </div>


          <span
            className={
              document.gemini_status ===
              "completed"
                ? "history-status completed"
                : "history-status processing"
            }
          >
            {document.gemini_status}
          </span>

        </div>


        <pre className="json-result">

          {document.structured_data
            ? JSON.stringify(
                document.structured_data,
                null,
                2
              )
            : document.gemini_status ===
              "pending"
            ? "Gemini extraction has not been completed yet."
            : "No structured data available."}

        </pre>

      </section>


      {/* ======================================================
          ERROR DETAILS
      ====================================================== */}

      {document.error_message && (

        <section className="card">

          <div className="card-header">

            <div>

              <h3>
                Processing Error
              </h3>

              <p>
                Error recorded during document
                processing.
              </p>

            </div>

          </div>


          <div className="error-message">

            {document.error_message}

          </div>

        </section>

      )}


      {/* ======================================================
          ACTIONS
      ====================================================== */}

      <section className="card">

        <div className="card-header">

          <div>

            <h3>
              Document Actions
            </h3>

            <p>
              Manage this document.
            </p>

          </div>

        </div>


        <div
          style={{
            display: "flex",
            gap: "12px",
            flexWrap: "wrap"
          }}
        >

          <button
            className="primary-button"
            onClick={handleReprocess}
            disabled={actionLoading}
          >
            {actionLoading
              ? "Processing..."
              : "Reprocess Document"}
          </button>


          <button
            className="secondary-button"
            onClick={handleDelete}
            disabled={actionLoading}
          >
            Delete Document
          </button>

        </div>

      </section>

    </div>
  );
}

export default DocumentDetails;