/**
 * 书法识文 — PWA 主逻辑
 * 拍照/选图 → 压缩 → 上传后端 → OCR 识别 → 展示/编辑 → 历史记录
 */

// ========== 配置 ==========
const API_BASE = (
    window.CALLIGRAPHY_API_BASE ||
    localStorage.getItem("api_base") ||
    "http://localhost:8000"
).replace(/\/$/, "");
const API_RECOGNIZE = `${API_BASE}/api/recognize`;
const MAX_IMAGE_WIDTH = 3000;
const JPEG_QUALITY = 0.92;
const HISTORY_KEY = "calligraphy_history";
const MAX_HISTORY = 50;
const REQUEST_TIMEOUT_MS = 300000;

// ========== DOM 引用 ==========
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const imageInput = $("#imageInput");
const galleryInput = $("#galleryInput");
const cameraBtn = $("#cameraBtn");
const galleryBtn = $("#galleryBtn");
const uploadArea = $("#uploadArea");
const previewArea = $("#previewArea");
const imagePreview = $("#imagePreview");
const retakeBtn = $("#retakeBtn");
const submitBtn = $("#submitBtn");
const cropDownloadBtn = $("#cropDownloadBtn");
const stepCapture = $("#step-capture");
const stepProcessing = $("#step-processing");
const stepResult = $("#step-result");
const stepHistory = $("#step-history");
const resultText = $("#resultText");
const resultMeta = $("#resultMeta");
const editToggleBtn = $("#editToggleBtn");
const editHint = $("#editHint");
const copyBtn = $("#copyBtn");
const newBtn = $("#newBtn");
const historyBtn = $("#historyBtn");
const backFromHistoryBtn = $("#backFromHistoryBtn");
const historyList = $("#historyList");
const clearHistoryBtn = $("#clearHistoryBtn");
const errorToast = $("#errorToast");
const steps = $$(".step");

// ========== 状态 ==========
let currentFile = null;
let currentDataUrl = null;

// ========== 步骤切换 ==========
function setStep(step) {
    [stepCapture, stepProcessing, stepResult, stepHistory].forEach((el, i) => {
        el.classList.toggle("active", i + 1 === step);
        el.classList.toggle("hidden", i + 1 !== step);
    });
    steps.forEach((el, i) => {
        el.classList.toggle("active", i + 1 === step);
    });
}

// ========== Toast ==========
function showToast(msg, duration = 3000) {
    errorToast.textContent = msg;
    errorToast.classList.remove("hidden");
    clearTimeout(window._toastTimer);
    window._toastTimer = setTimeout(() => {
        errorToast.classList.add("hidden");
    }, duration);
}

// ========== 图片压缩 ==========
function compressImage(file) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        const url = URL.createObjectURL(file);

        img.onload = () => {
            URL.revokeObjectURL(url);

            let { width, height } = img;
            if (width > MAX_IMAGE_WIDTH || height > MAX_IMAGE_WIDTH) {
                const ratio = MAX_IMAGE_WIDTH / Math.max(width, height);
                width = Math.round(width * ratio);
                height = Math.round(height * ratio);
            }

            const canvas = document.createElement("canvas");
            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext("2d");
            ctx.drawImage(img, 0, 0, width, height);

            canvas.toBlob((blob) => {
                if (!blob) {
                    reject("图片压缩失败");
                    return;
                }
                const compressedFile = new File([blob], "photo.jpg", {
                    type: "image/jpeg",
                });
                resolve(compressedFile);
            }, "image/jpeg", JPEG_QUALITY);
        };

        img.onerror = () => {
            URL.revokeObjectURL(url);
            reject("图片加载失败");
        };

        img.src = url;
    });
}

// ========== 图片加载 ==========
function loadImage(file) {
    return new Promise((resolve, reject) => {
        if (!file) return reject("无文件");

        const reader = new FileReader();
        reader.onload = (e) => {
            currentDataUrl = e.target.result;
            currentFile = file;
            resolve(e.target.result);
        };
        reader.onerror = () => reject("图片读取失败");
        reader.readAsDataURL(file);
    });
}

function showPreview(dataUrl) {
    imagePreview.src = dataUrl;
    uploadArea.classList.add("hidden");
    previewArea.classList.remove("hidden");
}

function resetToCapture() {
    uploadArea.classList.remove("hidden");
    previewArea.classList.add("hidden");
    currentFile = null;
    currentDataUrl = null;
    setStep(1);
}

// ========== 结果编辑 ==========
let isEditing = false;

function toggleEdit() {
    isEditing = !isEditing;
    resultText.contentEditable = isEditing;
    editToggleBtn.textContent = isEditing ? "💾 完成" : "✏️ 编辑";
    editHint.classList.toggle("hidden", !isEditing);
    if (isEditing) {
        resultText.focus();
    } else {
        resultText.blur();
    }
}

// ========== 复制 ==========
function copyResultText() {
    const text = resultText.textContent || resultText.innerText || "";
    if (!text || text === "（未识别到文字）") {
        showToast("没有可复制的内容");
        return;
    }
    navigator.clipboard.writeText(text)
        .then(() => showToast("已复制到剪贴板"))
        .catch(() => {
            const ta = document.createElement("textarea");
            ta.value = text;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand("copy");
            document.body.removeChild(ta);
            showToast("已复制到剪贴板");
        });
}

// ========== 历史记录 ==========
function getHistory() {
    try {
        return JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
    } catch {
        return [];
    }
}

function saveHistory(data) {
    const history = getHistory();
    const entry = {
        id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
        timestamp: new Date().toLocaleString("zh-CN"),
        text: data.text || "",
        totalLines: data.total_lines || 0,
    };
    history.unshift(entry);
    if (history.length > MAX_HISTORY) {
        history.length = MAX_HISTORY;
    }
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
}

function renderHistory() {
    const history = getHistory();
    if (history.length === 0) {
        historyList.innerHTML = '<p class="history-empty">暂无记录</p>';
        return;
    }

    historyList.innerHTML = history.map((item) => {
        const preview = (item.text || "").slice(0, 80);
        return `
            <div class="history-item" data-id="${item.id}">
                <div class="history-item-time">${item.timestamp} · ${item.totalLines} 行</div>
                <div class="history-item-text">${escapeHtml(preview)}</div>
                <div class="history-item-actions">
                    <button class="btn btn-sm view-history-btn" data-id="${item.id}">👁 查看</button>
                    <button class="btn btn-sm copy-history-btn" data-id="${item.id}">📋 复制</button>
                    <button class="btn btn-sm delete-history-btn" data-id="${item.id}">✕ 删除</button>
                </div>
            </div>
        `;
    }).join("");

    // 点击整条查看
    historyList.querySelectorAll(".history-item").forEach((el) => {
        el.addEventListener("click", (e) => {
            if (e.target.closest(".history-item-actions")) return;
            viewHistoryItem(el.dataset.id);
        });
    });

    // 查看按钮
    historyList.querySelectorAll(".view-history-btn").forEach((btn) => {
        btn.addEventListener("click", (e) => {
            e.stopPropagation();
            viewHistoryItem(btn.dataset.id);
        });
    });

    // 复制按钮
    historyList.querySelectorAll(".copy-history-btn").forEach((btn) => {
        btn.addEventListener("click", (e) => {
            e.stopPropagation();
            const history = getHistory();
            const item = history.find((h) => h.id === btn.dataset.id);
            if (item && item.text) {
                navigator.clipboard.writeText(item.text)
                    .then(() => showToast("已复制到剪贴板"))
                    .catch(() => showToast("复制失败"));
            }
        });
    });

    // 删除按钮
    historyList.querySelectorAll(".delete-history-btn").forEach((btn) => {
        btn.addEventListener("click", (e) => {
            e.stopPropagation();
            deleteHistoryItem(btn.dataset.id);
        });
    });
}

function viewHistoryItem(id) {
    const history = getHistory();
    const item = history.find((h) => h.id === id);
    if (!item) return;

    resultText.textContent = item.text || "（未识别到文字）";
    resultText.contentEditable = false;
    isEditing = false;
    editToggleBtn.textContent = "✏️ 编辑";
    editHint.classList.add("hidden");
    resultMeta.textContent = `共 ${item.totalLines || 0} 行 · 📜 历史记录`;
    setStep(3);
}

function deleteHistoryItem(id) {
    let history = getHistory();
    history = history.filter((h) => h.id !== id);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    renderHistory();
    showToast("已删除");
}

function clearAllHistory() {
    if (getHistory().length === 0) return;
    localStorage.removeItem(HISTORY_KEY);
    renderHistory();
    showToast("已清空全部记录");
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

async function pollRecognitionJob(jobId) {
    const deadline = Date.now() + REQUEST_TIMEOUT_MS;

    while (Date.now() < deadline) {
        await sleep(3000);
        const response = await fetch(`${API_RECOGNIZE}/${jobId}`);
        if (!response.ok) {
            throw new Error(`任务查询失败 (${response.status})`);
        }

        const data = await response.json();
        if (data.status === "done" || data.status === "failed") {
            return data;
        }
    }

    throw new DOMException("识别任务超时", "AbortError");
}

// ========== 事件 ==========

// 拍照
cameraBtn.addEventListener("click", () => imageInput.click());

imageInput.addEventListener("change", async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
        const dataUrl = await loadImage(file);
        showPreview(dataUrl);
    } catch (err) {
        showToast(err);
    }
    e.target.value = "";
});

// 相册
galleryBtn.addEventListener("click", () => galleryInput.click());

galleryInput.addEventListener("change", async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
        const dataUrl = await loadImage(file);
        showPreview(dataUrl);
    } catch (err) {
        showToast(err);
    }
    e.target.value = "";
});

// 重拍
retakeBtn.addEventListener("click", resetToCapture);

// 提交识别
submitBtn.addEventListener("click", async () => {
    if (!currentFile) {
        showToast("请先拍照或选择图片");
        return;
    }

    setStep(2);

    try {
        showToast("正在处理图片...", 10000);
        const compressedFile = await compressImage(currentFile);
        console.log("压缩后:", (compressedFile.size / 1024).toFixed(1) + "KB");

        const formData = new FormData();
        formData.append("file", compressedFile, "photo.jpg");

        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

        const response = await fetch(API_RECOGNIZE, {
            method: "POST",
            body: formData,
            signal: controller.signal,
        });
        clearTimeout(timeout);

        if (!response.ok) {
            throw new Error(`服务器错误 (${response.status})`);
        }

        let data = await response.json();
        if (data.job_id) {
            showToast("后端正在识别，请稍候...", 10000);
            data = await pollRecognitionJob(data.job_id);
        }

        setStep(3);

        if (!data.success) {
            resultText.textContent = data.error || "识别失败，请重试";
            resultText.style.color = "#c0392b";
            resultMeta.textContent = "";
            return;
        }

        resultText.textContent = data.text || "（未识别到文字）";
        resultText.style.color = "";
        resultText.contentEditable = false;
        isEditing = false;
        editToggleBtn.textContent = "✏️ 编辑";
        editHint.classList.add("hidden");
        resultMeta.textContent = `共识别 ${data.total_lines || 0} 行`;

        // 自动保存历史
        if (data.text) {
            saveHistory(data);
        }

    } catch (err) {
        console.error("识别出错:", err);
        setStep(1);
        if (err.name === "AbortError") {
            showToast("识别超时。免费后端或 OCR 模型启动较慢，请稍后重试");
        } else if (err.message.includes("fetch") || err.message.includes("NetworkError") || err.message.includes("Failed to fetch")) {
            showToast("后端连接中断。请稍后重试，或查看 Render Logs");
        } else {
            showToast(`识别出错: ${err.message}`);
        }
    }
});

// 编辑切换
editToggleBtn.addEventListener("click", toggleEdit);

// 复制
copyBtn.addEventListener("click", copyResultText);

// 识别下一张
newBtn.addEventListener("click", resetToCapture);

// 下载裁剪图
cropDownloadBtn.addEventListener("click", async () => {
    if (!currentFile) {
        showToast("请先拍照或选择图片");
        return;
    }

    try {
        const compressedFile = await compressImage(currentFile);
        const formData = new FormData();
        formData.append("file", compressedFile, "photo.jpg");

        const response = await fetch(`${API_BASE}/api/crop-image`, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`服务器错误 (${response.status})`);
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "calligraphy_cropped.jpg";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast("裁剪图已下载");
    } catch (err) {
        console.error("裁剪出错:", err);
        if (err.message.includes("fetch") || err.message.includes("Failed to fetch")) {
            showToast("网络连接失败，请确认后端已启动");
        } else {
            showToast(`裁剪失败: ${err.message}`);
        }
    }
});

// 查看历史
historyBtn.addEventListener("click", () => {
    renderHistory();
    setStep(4);
});

// 从历史返回拍照
backFromHistoryBtn.addEventListener("click", resetToCapture);

// 清空历史
clearHistoryBtn.addEventListener("click", () => {
    if (getHistory().length === 0) return;
    if (confirm("确定清空所有历史记录？")) {
        clearAllHistory();
    }
});

// 点击步骤栏的"历史"也可跳转
steps.forEach((step, i) => {
    if (i === 3) { // 第四个点是历史
        step.addEventListener("click", () => {
            renderHistory();
            setStep(4);
        });
    }
});

// ========== 初始化 ==========
setStep(1);

fetch(`${API_BASE}/health`)
    .then(r => r.json())
    .then(data => {
        console.log("后端连接成功:", data);
    })
    .catch(() => {
        console.warn("后端未连接，请确保服务已启动");
    });
