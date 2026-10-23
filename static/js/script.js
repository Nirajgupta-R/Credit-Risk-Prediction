
/* ==========================================
   CREDIT RISK DASHBOARD
   Charts, prediction animations and UI effects
========================================== */


/* ------------------------------------------
   1. CHART.JS DASHBOARD GRAPHS
------------------------------------------ */

document.addEventListener("DOMContentLoaded", function () {
    // Check whether Chart.js is loaded
    if (typeof Chart === "undefined") {
        console.error("Chart.js load nahi hua. CDN check karo.");
        return;
    }

    const predictionCanvas = document.getElementById("predictionChart");
    const probabilityCanvas = document.getElementById("probabilityChart");
    const scoreBandCanvas = document.getElementById("scoreBandChart");

    // The first two graphs are required on the dashboard.
    if (!predictionCanvas || !probabilityCanvas) {
        console.warn("Graph canvas nahi mila.");
        return;
    }

    let predictionData = [];
    let probabilityLabels = [];
    let probabilityData = [];

    try {
        predictionData = JSON.parse(
            predictionCanvas.dataset.values || "[0, 0]"
        );

        probabilityLabels = JSON.parse(
            probabilityCanvas.dataset.labels || "[]"
        );

        probabilityData = JSON.parse(
            probabilityCanvas.dataset.values || "[]"
        );
    } catch (error) {
        console.error("Graph data parse error:", error);
        return;
    }

    console.log("Prediction data:", predictionData);
    console.log("Probability labels:", probabilityLabels);
    console.log("Probability data:", probabilityData);

    // Graph 1: Prediction Distribution
    new Chart(predictionCanvas, {
        type: "doughnut",
        data: {
            labels: ["Default Risk", "No Default Risk"],
            datasets: [{
                data: predictionData,
                backgroundColor: ["#f87171", "#34d399"],
                borderColor: ["#141c2e", "#141c2e"],
                borderWidth: 3,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            animation: {
                duration: 1000,
                easing: "easeOutQuart"
            },
            plugins: {
                legend: {
                    position: "top",
                    labels: {
                        color: "#e2e8f0",
                        padding: 16
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return context.label + ": " + context.raw;
                        }
                    }
                }
            }
        }
    });

    // Graph 2: Default Probability for latest predictions
    new Chart(probabilityCanvas, {
        type: "bar",
        data: {
            labels: probabilityLabels,
            datasets: [{
                label: "Default Probability (%)",
                data: probabilityData,
                backgroundColor: "#78a6f5",
                borderRadius: 7,
                maxBarThickness: 55
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            animation: {
                duration: 1000,
                easing: "easeOutQuart"
            },
            scales: {
                x: {
                    ticks: {
                        color: "#cbd5e1"
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,
                    min: 0,
                    max: 100,
                    ticks: {
                        color: "#cbd5e1",
                        callback: function (value) {
                            return value + "%";
                        }
                    },
                    grid: {
                        color: "rgba(148, 163, 184, 0.15)"
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: "#e2e8f0"
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return "Default Probability: " +
                                context.raw + "%";
                        }
                    }
                }
            }
        }
    });

    // Graph 3: Current Applicant Prediction
    if (
        scoreBandCanvas &&
        scoreBandCanvas.dataset.probability !== undefined
    ) {
        const currentProbability = Math.min(
            100,
            Math.max(0, Number(scoreBandCanvas.dataset.probability) || 0)
        );

        const currentThreshold = Math.min(
            100,
            Math.max(0, Number(scoreBandCanvas.dataset.threshold) || 0)
        );

        const currentPrediction =
            scoreBandCanvas.dataset.prediction || "Prediction";

        const bandIndex = Math.min(
            4,
            Math.floor(currentProbability / 20)
        );

        const bandLabels = [
            "0–20%",
            "20–40%",
            "40–60%",
            "60–80%",
            "80–100%"
        ];

        const probabilityBandData = [null, null, null, null, null];
        probabilityBandData[bandIndex] = currentProbability;

        const thresholdData = [
            currentThreshold,
            currentThreshold,
            currentThreshold,
            currentThreshold,
            currentThreshold
        ];

        new Chart(scoreBandCanvas, {
            type: "bar",
            data: {
                labels: bandLabels,
                datasets: [
                    {
                        label: currentPrediction,
                        data: probabilityBandData,
                        backgroundColor: currentProbability >= currentThreshold
                            ? "#f87171"
                            : "#34d399",
                        borderColor: currentProbability >= currentThreshold
                            ? "#ef4444"
                            : "#10b981",
                        borderWidth: 1,
                        borderRadius: 8,
                        maxBarThickness: 65,
                        order: 1
                    },
                    {
                        type: "line",
                        label: "Decision Threshold",
                        data: thresholdData,
                        borderColor: "#fbbf24",
                        backgroundColor: "#fbbf24",
                        borderWidth: 2,
                        borderDash: [6, 4],
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: "#fbbf24",
                        tension: 0,
                        fill: false,
                        order: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                interaction: {
                    mode: "index",
                    intersect: false
                },
                animation: {
                    duration: 1000,
                    easing: "easeOutQuart"
                },
                scales: {
                    x: {
                        ticks: {
                            color: "#cbd5e1"
                        },
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        min: 0,
                        max: 100,
                        title: {
                            display: true,
                            text: "Probability (%)",
                            color: "#cbd5e1"
                        },
                        ticks: {
                            color: "#cbd5e1",
                            callback: function (value) {
                                return value + "%";
                            }
                        },
                        grid: {
                            color: "rgba(148, 163, 184, 0.15)"
                        }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: "#e2e8f0",
                            usePointStyle: true,
                            padding: 16
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                if (context.datasetIndex === 0) {
                                    if (context.raw == null) {
                                        return "No applicant bar in this band";
                                    }

                                    return currentPrediction + ": " +
                                        Number(context.raw).toFixed(2) + "%";
                                }

                                return "Decision Threshold: " +
                                    Number(context.raw).toFixed(2) + "%";
                            }
                        }
                    }
                }
            }
        });
    }

    console.log("Credit Risk charts initialized successfully.");
});


/* ------------------------------------------
   2. SCROLL TO PREDICTION RESULT
------------------------------------------ */

document.addEventListener("DOMContentLoaded", function () {
    const resultSection = document.getElementById("result");

    if (resultSection) {
        // Respect reduced-motion preference.
        const reducedMotion = window.matchMedia(
            "(prefers-reduced-motion: reduce)"
        ).matches;

        resultSection.scrollIntoView({
            behavior: reducedMotion ? "auto" : "smooth",
            block: "start"
        });
    }
});


/* ------------------------------------------
   3. ANIMATED PREDICTION PROBABILITY
------------------------------------------ */

document.addEventListener("DOMContentLoaded", function () {
    const probabilityElement = document.getElementById(
        "predictionProbability"
    );

    const progressFill = document.getElementById(
        "predictionProgressFill"
    );

    if (!probabilityElement || !progressFill) {
        return;
    }

    const probability = Math.min(
        100,
        Math.max(
            0,
            Number(probabilityElement.dataset.probability) || 0
        )
    );

    const prefersReducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches;

    const resultContainer = probabilityElement.closest(".result");
    const resultHeading = resultContainer?.querySelector("h2");

    const isDefaultRisk =
        resultHeading?.textContent.trim() === "Default Risk";

    progressFill.style.backgroundColor = isDefaultRisk
        ? "#f87171"
        : "#34d399";

    if (prefersReducedMotion) {
        probabilityElement.textContent = probability.toFixed(2) + "%";
        progressFill.style.width = probability + "%";
        return;
    }

    const duration = 1200;
    const startTime = performance.now();

    function animateProbability(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        const easedProgress = 1 - Math.pow(1 - progress, 3);
        const currentValue = probability * easedProgress;

        probabilityElement.textContent =
            currentValue.toFixed(2) + "%";

        if (progress < 1) {
            requestAnimationFrame(animateProbability);
        } else {
            probabilityElement.textContent =
                probability.toFixed(2) + "%";
        }
    }

    requestAnimationFrame(function () {
        progressFill.style.width = probability + "%";
    });

    requestAnimationFrame(animateProbability);
});


/* ------------------------------------------
   4. APPLICANT FORM — INTERACTIVE SUBMIT
   HTML unchanged
------------------------------------------ */

document.addEventListener("DOMContentLoaded", function () {
    const predictionForm = document.querySelector(
        '#prediction form[action*="predict"]'
    );

    const predictButton = document.getElementById("predictButton");

    if (!predictionForm || !predictButton) {
        return;
    }

    const buttonText = predictButton.querySelector(".button-text");
    const originalText = buttonText
        ? buttonText.textContent
        : "Predict Credit Risk →";

    // Add a visual focus class while users interact with form fields.
    const formFields = predictionForm.querySelectorAll("input, select");

    formFields.forEach(function (field) {
        field.addEventListener("focus", function () {
            field.closest(".form-grid > div")?.classList.add("field-active");
        });

        field.addEventListener("blur", function () {
            field.closest(".form-grid > div")?.classList.remove("field-active");
        });
    });

    predictionForm.addEventListener("submit", function (event) {
        // Do not show loading if browser validation fails.
        if (!predictionForm.checkValidity()) {
            return;
        }

        // Prevent accidental duplicate submissions.
        if (predictButton.disabled) {
            event.preventDefault();
            return;
        }

        predictButton.disabled = true;
        predictButton.classList.add("is-loading");
        predictButton.setAttribute("aria-busy", "true");

        if (buttonText) {
            buttonText.textContent = "Analyzing Risk...";
        }
    });

    // Restore button if the user returns to this page using browser history.
    window.addEventListener("pageshow", function () {
        predictButton.disabled = false;
        predictButton.classList.remove("is-loading");
        predictButton.removeAttribute("aria-busy");

        if (buttonText) {
            buttonText.textContent = originalText;
        }
    });
});


/* ------------------------------------------
   5. LIVE DATABASE STATISTICS COUNT-UP
------------------------------------------ */

document.addEventListener("DOMContentLoaded", function () {
    const statsSection = document.getElementById("liveStats");

    if (!statsSection) return;

    const counters = statsSection.querySelectorAll(".count-up");

    const reducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches;

    counters.forEach(function (counter) {
        const target = Number(counter.dataset.count);

        if (!Number.isFinite(target) || target < 0) return;

        if (reducedMotion) {
            counter.textContent = Math.round(target).toLocaleString();
            return;
        }

        const duration = 1100;
        let startTime = null;

        function animateCounter(timestamp) {
            if (startTime === null) startTime = timestamp;

            const progress = Math.min(
                (timestamp - startTime) / duration,
                1
            );

            const easedProgress = 1 - Math.pow(1 - progress, 4);
            const currentValue = Math.round(target * easedProgress);

            counter.textContent = currentValue.toLocaleString();

            if (progress < 1) {
                requestAnimationFrame(animateCounter);
            } else {
                counter.textContent = Math.round(target).toLocaleString();
            }
        }

        requestAnimationFrame(animateCounter);
    });
});


/* ------------------------------------------
   6. RECENT PREDICTIONS PROBABILITY BARS
------------------------------------------ */

document.addEventListener("DOMContentLoaded", function () {
    const recentSection = document.getElementById("recent-predictions");

    if (!recentSection) return;

    const probabilityBars = recentSection.querySelectorAll(
        ".probability-fill[data-width]"
    );

    const reducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches;

    probabilityBars.forEach(function (bar, index) {
        const probability = Number(bar.dataset.width);

        if (!Number.isFinite(probability)) return;

        const safeWidth = Math.min(100, Math.max(0, probability));

        if (reducedMotion) {
            bar.style.width = safeWidth + "%";
            return;
        }

        bar.style.width = "0%";

        window.setTimeout(function () {
            bar.style.width = safeWidth + "%";
        }, 180 + index * 100);
    });
});
