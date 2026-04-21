const compareButton = document.getElementById("compareButton");
const engineBadge = document.getElementById("engineBadge");
const boardStatus = document.getElementById("boardStatus");
const comparisonTable = document.getElementById("comparisonTable");
const overlay = document.getElementById("analysisOverlay");
const overlayTitle = document.getElementById("overlayTitle");
const overlayMode = document.getElementById("overlayMode");
const analysisContent = document.getElementById("analysisContent");
const closeOverlay = document.getElementById("closeOverlay");

const appState = {
  makes: [],
  years: [],
  cars: {
    left: { profile: null },
    right: { profile: null },
  },
};

function getPanelRefs(side) {
  return {
    year: document.getElementById(`${side}Year`),
    make: document.getElementById(`${side}Make`),
    model: document.getElementById(`${side}Model`),
    variant: document.getElementById(`${side}Variant`),
    title: document.getElementById(`${side}Title`),
    badge: document.getElementById(`${side}SpecBadge`),
    meta: document.getElementById(`${side}Meta`),
    image: document.getElementById(`${side}Image`),
    highlights: document.getElementById(`${side}Highlights`),
  };
}

const panels = {
  left: getPanelRefs("left"),
  right: getPanelRefs("right"),
};

function getCarImageUrl(make, model) {
  return `https://cdn.imagin.studio/getimage?customer=img-demo&make=${encodeURIComponent(make)}&modelFamily=${encodeURIComponent(model)}`;
}

function getFallbackImageUrl(make, model) {
  return `https://source.unsplash.com/featured/1200x800/?${encodeURIComponent(`${make} ${model} luxury car`)}`;
}

function populateSelect(select, options, placeholder, valueKey = "name", labelKey = "name") {
  select.innerHTML = "";

  const placeholderOption = document.createElement("option");
  placeholderOption.value = "";
  placeholderOption.textContent = placeholder;
  select.appendChild(placeholderOption);

  options.forEach((option) => {
    const element = document.createElement("option");
    element.value = option[valueKey];
    element.textContent = option[labelKey];
    select.appendChild(element);
  });

  select.value = "";
}

function setSelectLoading(select, label) {
  select.innerHTML = "";
  const option = document.createElement("option");
  option.value = "";
  option.textContent = label;
  select.appendChild(option);
}

function resetSelect(select, placeholder, disabled = true) {
  populateSelect(select, [], placeholder);
  select.disabled = disabled;
}

async function apiGet(path, params = {}) {
  const query = new URLSearchParams(params);
  const url = query.toString() ? `${path}?${query.toString()}` : path;
  const response = await fetch(url);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Request failed.");
  }
  return payload;
}

async function apiPost(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Request failed.");
  }
  return payload;
}

function renderVehicleImage(side, make, model) {
  const image = panels[side].image;
  image.classList.remove("loaded");
  image.src = getCarImageUrl(make, model);
  image.onerror = () => {
    image.onerror = null;
    image.src = getFallbackImageUrl(make, model);
  };
  image.onload = () => {
    image.classList.add("loaded");
  };
}

function renderHighlights(side, profile) {
  const container = panels[side].highlights;
  container.innerHTML = "";

  const highlightSpecs = (profile.display_specs || []).slice(0, 4);
  if (!highlightSpecs.length) {
    const empty = document.createElement("div");
    empty.className = "empty-card";
    empty.textContent = "Detailed specs are not available for this selection yet.";
    container.appendChild(empty);
    return;
  }

  highlightSpecs.forEach((item) => {
    const card = document.createElement("article");
    card.className = "highlight-card";

    const label = document.createElement("span");
    label.textContent = item.label;

    const value = document.createElement("strong");
    value.textContent = item.value;

    card.appendChild(label);
    card.appendChild(value);
    container.appendChild(card);
  });
}

function renderCarProfile(side, profile) {
  const panel = panels[side];
  appState.cars[side].profile = profile;

  panel.title.textContent = `${profile.make} ${profile.model}`;
  panel.badge.textContent = profile.has_detailed_specs ? "Detailed specs loaded" : "Fallback profile";
  panel.meta.textContent = `${profile.year} ${profile.variant} • ${profile.source}`;
  renderVehicleImage(side, profile.make, profile.model);
  renderHighlights(side, profile);
  renderComparisonTable();
  updateCompareButton();
}

function buildSpecMap(profile) {
  const map = {};
  (profile?.display_specs || []).forEach((item) => {
    map[item.label] = item.value;
  });
  return map;
}

function renderComparisonTable() {
  const left = appState.cars.left.profile;
  const right = appState.cars.right.profile;

  if (!left && !right) {
    comparisonTable.innerHTML = '<div class="table-empty">Your side-by-side spec matrix will appear here.</div>';
    boardStatus.textContent = "Select two cars to compare";
    return;
  }

  const leftMap = buildSpecMap(left);
  const rightMap = buildSpecMap(right);
  const labels = [];

  [left?.display_specs || [], right?.display_specs || []].forEach((list) => {
    list.forEach((item) => {
      if (!labels.includes(item.label)) {
        labels.push(item.label);
      }
    });
  });

  if (!labels.length) {
    comparisonTable.innerHTML = '<div class="table-empty">Specs are limited for the current selection.</div>';
    boardStatus.textContent = "Limited spec coverage";
    return;
  }

  comparisonTable.innerHTML = "";

  const head = document.createElement("div");
  head.className = "table-head";
  head.innerHTML = `
    <div class="table-label">Specification</div>
    <div class="table-label">${left ? `${left.make} ${left.model}` : "Vehicle A"}</div>
    <div class="table-label">${right ? `${right.make} ${right.model}` : "Vehicle B"}</div>
  `;
  comparisonTable.appendChild(head);

  labels.forEach((label) => {
    const row = document.createElement("div");
    row.className = "table-row";

    const name = document.createElement("div");
    name.className = "table-label";
    name.textContent = label;

    const leftValue = document.createElement("div");
    leftValue.className = "table-value";
    leftValue.textContent = leftMap[label] || "—";

    const rightValue = document.createElement("div");
    rightValue.className = "table-value";
    rightValue.textContent = rightMap[label] || "—";

    row.appendChild(name);
    row.appendChild(leftValue);
    row.appendChild(rightValue);
    comparisonTable.appendChild(row);
  });

  boardStatus.textContent = left && right ? "Live spec comparison ready" : "Add another car to complete the table";
}

function updateCompareButton() {
  const ready = Boolean(appState.cars.left.profile && appState.cars.right.profile);
  compareButton.disabled = !ready;
}

async function loadModels(side) {
  const panel = panels[side];
  const year = panel.year.value;
  const make = panel.make.value;

  resetSelect(panel.model, "Select model", true);
  resetSelect(panel.variant, "Select variant", true);
  appState.cars[side].profile = null;
  renderComparisonTable();
  updateCompareButton();

  if (!year || !make) {
    return;
  }

  setSelectLoading(panel.model, "Loading models...");
  panel.model.disabled = true;

  try {
    const payload = await apiGet("/api/models", { year, make });
    populateSelect(panel.model, payload.models || [], "Select model");
    panel.model.disabled = false;
  } catch (error) {
    setSelectLoading(panel.model, "Models unavailable");
    panel.meta.textContent = error.message;
  }
}

async function loadVariants(side) {
  const panel = panels[side];
  const year = panel.year.value;
  const make = panel.make.value;
  const model = panel.model.value;

  resetSelect(panel.variant, "Select variant", true);
  appState.cars[side].profile = null;
  renderComparisonTable();
  updateCompareButton();

  if (!year || !make || !model) {
    return;
  }

  setSelectLoading(panel.variant, "Loading variants...");
  panel.variant.disabled = true;

  try {
    const payload = await apiGet("/api/variants", { year, make, model });
    populateSelect(panel.variant, payload.variants || [], "Select variant");
    panel.variant.disabled = false;

    const firstVariant = payload.variants?.[0]?.name;
    if (firstVariant) {
      panel.variant.value = firstVariant;
      await loadCarProfile(side);
    }
  } catch (error) {
    setSelectLoading(panel.variant, "Variants unavailable");
    panel.meta.textContent = error.message;
  }
}

async function loadCarProfile(side) {
  const panel = panels[side];
  const year = panel.year.value;
  const make = panel.make.value;
  const model = panel.model.value;
  const variant = panel.variant.value;

  if (!year || !make || !model) {
    return;
  }

  panel.badge.textContent = "Loading profile";
  panel.meta.textContent = "Fetching technical specs...";

  try {
    const payload = await apiGet("/api/car-specs", { year, make, model, variant });
    renderCarProfile(side, payload.car);
  } catch (error) {
    panel.badge.textContent = "Load failed";
    panel.meta.textContent = error.message;
  }
}

function openOverlay() {
  overlay.classList.remove("hidden");
  overlay.setAttribute("aria-hidden", "false");
  document.body.classList.add("overlay-open");
}

function closeOverlayPanel() {
  overlay.classList.add("hidden");
  overlay.setAttribute("aria-hidden", "true");
  document.body.classList.remove("overlay-open");
}

async function handleCompare() {
  const left = appState.cars.left.profile;
  const right = appState.cars.right.profile;
  if (!left || !right) {
    return;
  }

  compareButton.disabled = true;
  compareButton.textContent = "Comparing...";

  try {
    const payload = await apiPost("/api/compare", { car1: left, car2: right });
    overlayTitle.textContent = `${left.make} ${left.model} vs ${right.make} ${right.model}`;
    overlayMode.textContent = payload.groq_configured ? `Groq • ${payload.model}` : "Local preview";
    analysisContent.textContent = payload.analysis;
    openOverlay();
  } catch (error) {
    overlayTitle.textContent = "Comparison unavailable";
    overlayMode.textContent = "Error";
    analysisContent.textContent = error.message;
    openOverlay();
  } finally {
    compareButton.disabled = false;
    compareButton.textContent = "Compare with AI";
    updateCompareButton();
  }
}

function bindPanel(side) {
  const panel = panels[side];

  panel.year.addEventListener("change", () => {
    appState.cars[side].profile = null;
    populateSelect(panel.make, appState.makes, "Select make");
    panel.make.disabled = false;
    resetSelect(panel.model, "Select model", true);
    resetSelect(panel.variant, "Select variant", true);
    panel.title.textContent = "Select a car";
    panel.badge.textContent = "Awaiting make";
    panel.meta.textContent = "Choose a make to continue.";
    panel.highlights.innerHTML = '<div class="empty-card">No specs yet.</div>';
    renderComparisonTable();
    updateCompareButton();
  });

  panel.make.addEventListener("change", async () => {
    panel.badge.textContent = "Loading models";
    panel.meta.textContent = "Looking up available models...";
    await loadModels(side);
  });

  panel.model.addEventListener("change", async () => {
    panel.badge.textContent = "Loading variants";
    panel.meta.textContent = "Looking up available trims and body styles...";
    await loadVariants(side);
  });

  panel.variant.addEventListener("change", async () => {
    await loadCarProfile(side);
  });
}

async function initialize() {
  bindPanel("left");
  bindPanel("right");
  compareButton.addEventListener("click", handleCompare);
  closeOverlay.addEventListener("click", closeOverlayPanel);
  overlay.addEventListener("click", (event) => {
    if (event.target === overlay || event.target.classList.contains("overlay-backdrop")) {
      closeOverlayPanel();
    }
  });

  try {
    const [health, yearsPayload, makesPayload] = await Promise.all([
      apiGet("/health"),
      apiGet("/api/years"),
      apiGet("/api/makes"),
    ]);

    engineBadge.textContent = health.groq_configured ? `Groq Ready • ${health.model}` : `Groq Not Configured • ${health.model}`;
    appState.years = yearsPayload.years || [];
    appState.makes = makesPayload.makes || [];

    ["left", "right"].forEach((side) => {
      const panel = panels[side];
      populateSelect(
        panel.year,
        appState.years.map((year) => ({ name: String(year) })),
        "Select year"
      );
      panel.year.value = String(appState.years[0] || "");
      panel.year.dispatchEvent(new Event("change"));
    });
  } catch (error) {
    engineBadge.textContent = "Startup Error";
    boardStatus.textContent = error.message;
  }
}

initialize();
