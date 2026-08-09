import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const API_URL = "http://127.0.0.1:8000";

function DocumentIntelligence() {
  const navigate = useNavigate();

  const [selectedFile, setSelectedFile] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [processingId, setProcessingId] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  // ============================================================
  // File Selection
  // ============================================================

  const handleFileChange = (event) => {
    const file = event.target.files[0];

    if (file) {
      setSelectedFile(file);
      setResult(null);
      setProcessingId(null);
      setError("");
    }
  };

  // ============================================================
  // Poll Processing Status
  // ============================================================

  const pollProcessingStatus = async (id) => {
    const maxAttempts = 60;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        const response = await axios.get(
          `${API_URL}/documents/${id}`
        );

        const data = response.data;

        console.log("Processing status:", data);

        setResult(data);

        // ----------------------------------------------------
        // Processing completed
        // ----------------------------------------------------

        if (data.status === "completed") {
          setProcessing(false);
          return;
        }

        // ----------------------------------------------------
        // Processing failed
        // ----------------------------------------------------

        if (data.status === "failed") {
          setProcessing(false);

          setError(
            data.error_message ||
              "Invoice processing failed."
          );

          return;
        }

        // ----------------------------------------------------
        // Still processing
        // ----------------------------------------------------

        await new Promise((resolve) =>
          setTimeout(resolve, 2000)
        );
      } catch (err) {
        console.error(
          "Status polling error:",
          err
        );

        setProcessing(false);

        setError(
          "Could not retrieve invoice processing status."
        );

        return;
      }
    }

    // --------------------------------------------------------
    // Timeout
    // --------------------------------------------------------

    setProcessing(false);

    setError(
      "Invoice processing is taking too long. Please check the Logs or try again."
    );
  };

  // ============================================================
  // Process Invoice
  // ============================================================

  const handleProcess = async () => {
    if (!selectedFile) {
      setError(
        "Please select an invoice first."
      );

      return;
    }

    setProcessing(true);
    setError("");
    setResult(null);
    setProcessingId(null);

    try {
      // ------------------------------------------------------
      // Create FormData
      // ------------------------------------------------------

      const formData = new FormData();

      formData.append(
        "file",
        selectedFile
      );

      // ------------------------------------------------------
      // Upload Invoice
      // ------------------------------------------------------

      const response = await axios.post(
        `${API_URL}/upload`,
        formData,
        {
          headers: {
            "Content-Type":
              "multipart/form-data",
          },
        }
      );

      console.log(
        "Upload response:",
        response.data
      );

      // ------------------------------------------------------
      // Get Processing ID
      // ------------------------------------------------------

      const id =
        response.data.processing_id;

      if (!id) {
        throw new Error(
          "Backend did not return a processing ID."
        );
      }

      setProcessingId(id);

      // ------------------------------------------------------
      // Show initial queued status
      // ------------------------------------------------------

      setResult({
        id: id,
        filename:
          response.data.filename,
        status: "queued",
        ocr_status: "pending",
        docling_status: "pending",
        gemini_status: "pending",
        ocr_text: null,
        structured_data: null,
        request_id: null,
        error_message: null,
      });

      // ------------------------------------------------------
      // Start polling
      // ------------------------------------------------------

      await pollProcessingStatus(id);

    } catch (err) {
      console.error(
        "Upload error:",
        err
      );

      if (err.response) {
        setError(
          err.response.data?.detail ||
            `Server error: ${err.response.status}`
        );
      } else {
        setError(
          err.message ||
            "Could not connect to the backend. Make sure FastAPI is running on port 8000."
        );
      }

      setProcessing(false);
    }
  };

  // ============================================================
  // Pipeline Step Helpers
  // ============================================================

  const isUploaded = () => {
    return selectedFile !== null;
  };

  const isQueued = () => {
    return (
      result &&
      (
        result.status === "queued" ||
        result.status === "processing" ||
        result.status === "completed"
      )
    );
  };

  const isOCRCompleted = () => {
    return (
      result &&
      (
        result.ocr_status === "completed" ||
        result.docling_status === "completed" ||
        result.gemini_status === "completed" ||
        result.status === "completed"
      )
    );
  };

  const isDoclingCompleted = () => {
    return (
      result &&
      (
        result.docling_status === "completed" ||
        result.gemini_status === "completed" ||
        result.status === "completed"
      )
    );
  };

  const isGeminiCompleted = () => {
    return (
      result &&
      (
        result.gemini_status === "completed" ||
        result.status === "completed"
      )
    );
  };

  const isDatabaseCompleted = () => {
    return (
      result &&
      result.status === "completed"
    );
  };

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
            Document Intelligence
          </h2>

          <p>
            Upload and process procurement
            invoices using OCR and AI.
          </p>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
          }}
        >

          {/* Document History */}

          <button
            className="secondary-button"
            onClick={() =>
              navigate("/documents/history")
            }
          >
            Document History
          </button>

          {/* Agent Status */}

          <div className="agent-status">

            <span className="status-dot"></span>

            Agent Online

          </div>

        </div>

      </div>


      {/* ======================================================
          UPLOAD
      ====================================================== */}

      <section className="card upload-card">

        <div className="card-header">

          <div>

            <h3>
              Upload Procurement Document
            </h3>

            <p>
              Upload an invoice in PDF, PNG,
              JPG, or JPEG format.
            </p>

          </div>

        </div>


        <label className="upload-area">

          <div className="upload-icon">
            DOC
          </div>

          <h3>
            {selectedFile
              ? selectedFile.name
              : "Drop your invoice here"}
          </h3>

          <p>
            or click to browse your computer
          </p>

          <input
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            onChange={handleFileChange}
          />

        </label>


        {/* ==================================================
            SELECTED FILE
        ================================================== */}

        {selectedFile && (

          <div className="selected-file">

            <div>

              <strong>
                {selectedFile.name}
              </strong>

              <span>
                {(selectedFile.size / 1024).toFixed(1)} KB
              </span>

            </div>


            <button
              className="primary-button"
              onClick={handleProcess}
              disabled={processing}
            >
              {processing
                ? "Processing..."
                : "Process Invoice"}
            </button>

          </div>

        )}


        {/* ==================================================
            ERROR
        ================================================== */}

        {error && (

          <div className="error-message">
            {error}
          </div>

        )}

      </section>


      {/* ======================================================
          PROCESSING STATUS
      ====================================================== */}

      <section className="card">

        <div className="card-header">

          <div>

            <h3>
              Processing Status
            </h3>

            <p>
              Current invoice processing pipeline
            </p>

          </div>

        </div>


        <div className="pipeline">


          {/* STEP 1 — UPLOADED */}

          <div
            className={`pipeline-step ${
              isUploaded()
                ? "completed"
                : ""
            }`}
          >

            <div className="step-circle">

              {isUploaded()
                ? "✓"
                : "1"}

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


          {/* STEP 2 — QUEUED */}

          <div
            className={`pipeline-step ${
              isQueued()
                ? "completed"
                : ""
            }`}
          >

            <div className="step-circle">

              {isQueued()
                ? "✓"
                : "2"}

            </div>

            <div>

              <strong>
                Queued
              </strong>

              <span>
                Waiting in Kafka
              </span>

            </div>

          </div>


          <div className="pipeline-line"></div>


          {/* STEP 3 — OCR */}

          <div
            className={`pipeline-step ${
              isOCRCompleted()
                ? "completed"
                : ""
            }`}
          >

            <div className="step-circle">

              {isOCRCompleted()
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


          {/* STEP 4 — DOCLING */}

          <div
            className={`pipeline-step ${
              isDoclingCompleted()
                ? "completed"
                : ""
            }`}
          >

            <div className="step-circle">

              {isDoclingCompleted()
                ? "✓"
                : "4"}

            </div>

            <div>

              <strong>
                Docling
              </strong>

              <span>
                Document structure
              </span>

            </div>

          </div>


          <div className="pipeline-line"></div>


          {/* STEP 5 — AI EXTRACTION */}

          <div
            className={`pipeline-step ${
              isGeminiCompleted()
                ? "completed"
                : ""
            }`}
          >

            <div className="step-circle">

              {isGeminiCompleted()
                ? "✓"
                : "5"}

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


          {/* STEP 6 — DATABASE */}

          <div
            className={`pipeline-step ${
              isDatabaseCompleted()
                ? "completed"
                : ""
            }`}
          >

            <div className="step-circle">

              {isDatabaseCompleted()
                ? "✓"
                : "6"}

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
          RESULTS
      ====================================================== */}

      {result && (

        <>

          {/* ==================================================
              TWO COLUMN INFORMATION
          ================================================== */}

          <div className="two-column">


            {/* EXTRACTED INFORMATION */}

            <section className="card">

              <div className="card-header">

                <div>

                  <h3>
                    Extracted Information
                  </h3>

                  <p>
                    Structured invoice information
                  </p>

                </div>

              </div>


              <div className="information-grid">


                <div>

                  <span>
                    Processing ID
                  </span>

                  <strong>
                    {result.id ??
                      processingId ??
                      "—"}
                  </strong>

                </div>


                <div>

                  <span>
                    Request ID
                  </span>

                  <strong>
                    {result.request_id ??
                      "Pending"}
                  </strong>

                </div>


                <div>

                  <span>
                    Filename
                  </span>

                  <strong>
                    {result.filename ??
                      selectedFile?.name ??
                      "—"}
                  </strong>

                </div>


                <div>

                  <span>
                    Status
                  </span>

                  <strong>
                    {result.status ??
                      "—"}
                  </strong>

                </div>


                <div>

                  <span>
                    OCR
                  </span>

                  <strong>
                    {result.ocr_status ??
                      "pending"}
                  </strong>

                </div>


                <div>

                  <span>
                    Docling
                  </span>

                  <strong>
                    {result.docling_status ??
                      "pending"}
                  </strong>

                </div>


                <div>

                  <span>
                    Gemini
                  </span>

                  <strong>
                    {result.gemini_status ??
                      "pending"}
                  </strong>

                </div>

              </div>

            </section>


            {/* AGENT ACTIVITY */}

            <section className="card">

              <div className="card-header">

                <div>

                  <h3>
                    Agent Activity
                  </h3>

                  <p>
                    Latest processing events
                  </p>

                </div>

              </div>


              <div className="activity">


                <div>

                  <span className="activity-dot"></span>

                  <p>
                    Invoice uploaded
                  </p>

                </div>


                {result.status !== "queued" && (

                  <div>

                    <span className="activity-dot"></span>

                    <p>
                      Kafka event received
                    </p>

                  </div>

                )}


                {result.ocr_status ===
                  "completed" && (

                  <div>

                    <span className="activity-dot"></span>

                    <p>
                      Tesseract OCR completed
                    </p>

                  </div>

                )}


                {result.docling_status ===
                  "completed" && (

                  <div>

                    <span className="activity-dot"></span>

                    <p>
                      Docling document structure extracted
                    </p>

                  </div>

                )}


                {result.gemini_status ===
                  "completed" && (

                  <div>

                    <span className="activity-dot"></span>

                    <p>
                      Gemini extraction completed
                    </p>

                  </div>

                )}


                {result.status ===
                  "completed" && (

                  <div>

                    <span className="activity-dot"></span>

                    <p>
                      Saved to PostgreSQL
                    </p>

                  </div>

                )}


                {result.status ===
                  "failed" && (

                  <div>

                    <span className="activity-dot"></span>

                    <p>
                      Processing failed
                    </p>

                  </div>

                )}

              </div>

            </section>

          </div>


          {/* ==================================================
              OCR TEXT
          ================================================== */}

          <section className="card">

            <div className="card-header">

              <div>

                <h3>
                  OCR Text
                </h3>

                <p>
                  Text extracted from the invoice
                </p>

              </div>

            </div>


            <div className="ocr-result">

              {result.ocr_text
                ? result.ocr_text
                : result.ocr_status ===
                  "pending"
                ? "OCR processing..."
                : "No OCR text returned."}

            </div>

          </section>


          {/* ==================================================
              STRUCTURED DATA
          ================================================== */}

          <section className="card">

            <div className="card-header">

              <div>

                <h3>
                  Structured Data
                </h3>

                <p>
                  Information extracted by Gemini
                </p>

              </div>

            </div>


            <pre className="json-result">

              {result.structured_data
                ? JSON.stringify(
                    result.structured_data,
                    null,
                    2
                  )
                : result.gemini_status ===
                  "pending"
                ? "Gemini processing..."
                : "No structured data returned."}

            </pre>

          </section>


          {/* ==================================================
              VIEW CURRENT DOCUMENT
          ================================================== */}

          {processingId && (

            <section className="card">

              <div className="card-header">

                <div>

                  <h3>
                    Document Actions
                  </h3>

                  <p>
                    View this document in the
                    processing history.
                  </p>

                </div>

              </div>


              <button
                className="secondary-button"
                onClick={() =>
                  navigate(
                    `/documents/${processingId}`
                  )
                }
              >
                View Document Details
              </button>

            </section>

          )}

        </>

      )}

    </div>
  );
}

export default DocumentIntelligence;