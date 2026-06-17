import {apiService, state} from "../index.mjs";

const createBloom = (template, bloom) => {
  if (!bloom) return;
  const bloomFrag = document.getElementById(template).content.cloneNode(true);
  const bloomParser = new DOMParser();

  const bloomArticle = bloomFrag.querySelector("[data-bloom]");
  const bloomUsername = bloomFrag.querySelector("[data-username]");
  const bloomTime = bloomFrag.querySelector("[data-time]");
  const bloomTimeLink = bloomFrag.querySelector("a:has(> [data-time])");
  const bloomContent = bloomFrag.querySelector("[data-content]");
  const rebloamAttribution = bloomFrag.querySelector("[data-rebloom-attribution]");
  const originalSenderLink = bloomFrag.querySelector("[data-original-sender]");
  const rebloomButton = bloomFrag.querySelector("[data-action='rebloom']");
  const rebloomCount = bloomFrag.querySelector("[data-rebloom-count]");

  bloomArticle.setAttribute("data-bloom-id", bloom.id);
  bloomUsername.setAttribute("href", `/#/profile/${bloom.sender}`);
  bloomUsername.textContent = bloom.sender;
  bloomTime.textContent = _formatTimestamp(bloom.sent_timestamp);
  bloomTimeLink.setAttribute("href", `/#/bloom/${bloom.id}`);
  bloomContent.replaceChildren(
    ...bloomParser.parseFromString(_formatHashtags(bloom.content), "text/html")
      .body.childNodes
  );

  if (bloom.original_sender) {
    rebloamAttribution.hidden = false;
    originalSenderLink.textContent = bloom.original_sender;
    originalSenderLink.setAttribute("href", `/#/profile/${bloom.original_sender}`);
  }

  if (bloom.rebloom_count > 0) {
    rebloomCount.hidden = false;
    rebloomCount.textContent = `${bloom.rebloom_count} rebloom${bloom.rebloom_count === 1 ? "" : "s"}`;
  }

  rebloomButton.setAttribute("data-bloom-id", bloom.id);
  if (!state.isLoggedIn) {
    rebloomButton.style.display = "none";
  } else {
    rebloomButton.addEventListener("click", handleRebloom);
  }

  return bloomFrag;
};

async function handleRebloom(event) {
  const button = event.target;
  const bloomId = button.getAttribute("data-bloom-id");
  if (!bloomId) return;

  await apiService.rebloom(bloomId);
}

function _formatHashtags(text) {
  if (!text) return text;
  return text.replace(
    /\B#\w+/g,
    (match) => `<a href="/hashtag/${match.slice(1)}">${match}</a>`
  );
}

function _formatTimestamp(timestamp) {
  if (!timestamp) return "";

  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffSeconds = Math.floor((now - date) / 1000);

    if (diffSeconds < 60) {
      return `${diffSeconds}s`;
    }

    const diffMinutes = Math.floor(diffSeconds / 60);
    if (diffMinutes < 60) {
      return `${diffMinutes}m`;
    }

    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) {
      return `${diffHours}h`;
    }

    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) {
      return `${diffDays}d`;
    }

    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
    }).format(date);
  } catch (error) {
    console.error("Failed to format timestamp:", error);
    return "";
  }
}

export {createBloom};
