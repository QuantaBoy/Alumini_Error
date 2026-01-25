document.addEventListener("DOMContentLoaded", () => {
  // ==============================
  // 1. SMART SCROLL ANIMATION
  // ==============================
  const navbar = document.querySelector(".navbar");
  const body = document.body;

  if (navbar) {
    window.addEventListener("scroll", () => {
      const scrollY = window.scrollY;

      // Navbar Transformation
      if (scrollY > 50) {
        navbar.classList.add("scrolled");
        body.classList.add("nav-scrolled");
      } else {
        navbar.classList.remove("scrolled");
        body.classList.remove("nav-scrolled");
        body.classList.remove("content-scrolled");
      }

      // Intelligent Layout Expansion
      const leftPanel = document.querySelector(".left-panel");
      const rightPanel = document.querySelector(".right-panel");

      // Cache the height when content is visible to avoid reading 0 when hidden
      if (!body.classList.contains("content-scrolled")) {
        window.lastSideHeight = Math.max(
          leftPanel ? leftPanel.offsetHeight : 0,
          rightPanel ? rightPanel.offsetHeight : 0
        );
      }

      const sideHeight = window.lastSideHeight || 0;

      const triggerPointEntry = sideHeight - 50;
      const triggerPointExit = sideHeight - 150;

      if (sideHeight > 0) { // Only run if we have a valid height
        if (scrollY > triggerPointEntry) {
          if (!body.classList.contains("content-scrolled")) {
            body.classList.add("content-scrolled");
          }
        } else if (scrollY < triggerPointExit) {
          if (body.classList.contains("content-scrolled")) {
            body.classList.remove("content-scrolled");
          }
        }
      }
    });
  }

  // ==============================
  // 2. FILE UPLOAD HANDLERS
  // ==============================
  const actionButtons = document.querySelectorAll('.action-btn');
  const fileInput = document.getElementById('file');

  // Debug Log
  console.log('File Upload Setup:', {
    buttons: actionButtons.length,
    input: !!fileInput
  });

  if (actionButtons && fileInput) {
    actionButtons.forEach((btn, index) => {
      // 0 = Image, 1 = Video
      if (index === 0 || index === 1) {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          console.log(`Action Button ${index} Clicked`);
          fileInput.click();
        });
      }
    });

    // Log Selection
    fileInput.addEventListener('change', (e) => {
      console.log('Files Selected:', e.target.files.length);
    });
  }

  // ==============================
  // 3. POST SUBMISSION HANDLER
  // ==============================
  const postBtn = document.getElementById("postBtn");
  if (postBtn) {
    postBtn.addEventListener("click", createPost);
  }

  // Allow Enter key to submit (Shift+Enter for duplicate)
  const postInput = document.getElementById("content");
  if (postInput) {
    postInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        createPost();
      }
    });
  }

  // ==============================
  // 4. LOAD POSTS ON INIT
  // ==============================
  const postsContainer = document.getElementById("postsContainer");
  if (postsContainer) {
    loadPosts();
  }

  // Close menus when clicking outside
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".post-menu")) {
      document.querySelectorAll(".menu-dropdown").forEach(m => m.style.display = "none");
    }
  });

  // ==============================
  // 5. SMOOTH SCROLL TO TOP
  // ==============================
  const homeIcon = document.querySelector("#home-icon");
  if (homeIcon) {
    homeIcon.addEventListener("click", (e) => {
      // Check if we are already on the home page (or close enough)
      // Since this script is likely only loaded on home or it's the home icon:
      e.preventDefault();
      window.scrollTo({
        top: 0,
        behavior: "smooth"
      });
    });
  }

  // ==============================
  // 6. SIDEBAR TOGGLE (Hamburger Menu)
  // ==============================
  const menuIcon = document.querySelector(".nav-menu-icon");
  const leftPanel = document.querySelector(".left-panel");
  const wrapper = document.querySelector(".wrapper"); // Optional: logic might involve wrapper

  if (menuIcon && leftPanel) {
    menuIcon.addEventListener("click", (e) => {
      e.stopPropagation(); // Prevent document click from closing immediately if used
      leftPanel.classList.toggle("active");

      // Optional: If 'active' style isn't defined, we might need basic logic to show it
      // But user said "only logic not css", so we assume css class 'active' handles it.
      console.log("Sidebar toggled:", leftPanel.classList.contains("active"));
    });

    // Close on click outside
    document.addEventListener("click", (e) => {
      if (leftPanel.classList.contains("active") &&
        !leftPanel.contains(e.target) &&
        !menuIcon.contains(e.target)) {
        leftPanel.classList.remove("active");
      }
    });
  }

  // ==============================
  // 7. PROFILE DROPDOWN TOGGLE
  // ==============================
  const profileContainer = document.getElementById("navProfileContainer");
  const profileDropdown = document.getElementById("profileDropdown");

  if (profileContainer && profileDropdown) {
    profileContainer.addEventListener("click", (e) => {
      e.stopPropagation();
      profileDropdown.classList.toggle("show");
    });

    // Close when clicking outside
    document.addEventListener("click", (e) => {
      if (!profileContainer.contains(e.target)) {
        profileDropdown.classList.remove("show");
      }
    });
  }

}); // END DOMContentLoaded


// ==============================
// HELPER FUNCTIONS
// ==============================

function timeAgo(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const seconds = Math.floor((now - date) / 1000);

  if (seconds < 60) return "Just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);

  if (days < 7) return `${days}d ago`;
  if (days < 30) return `${Math.floor(days / 7)}w ago`;
  if (days < 365) return `${Math.floor(days / 30)}mo ago`;
  return `${Math.floor(days / 365)}y ago`;
}

async function createPost() {
  const content = document.getElementById("content").value.trim();
  const fileInput = document.getElementById("file");
  const files = fileInput ? fileInput.files : [];

  console.log("=== CREATE POST TRIGGERED ===");

  if (!content && files.length === 0) {
    alert("Please enter content or select a file to post.");
    return;
  }

  const formData = new FormData();
  formData.append("content", content);
  for (let i = 0; i < files.length; i++) {
    formData.append("files", files[i]);
  }

  try {
    const res = await fetch("/api/posts", {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.message || "Failed to create post.");
    }

    console.log("Post Created!");
    document.getElementById("content").value = "";
    if (fileInput) fileInput.value = "";
    loadPosts();

  } catch (err) {
    console.error("Post Error:", err);
    alert("Error: " + err.message);
  }
}

async function loadPosts() {
  const postsContainer = document.getElementById("postsContainer");
  if (!postsContainer) return;

  try {
    const res = await fetch("/api/posts");
    if (!res.ok) throw new Error("Failed to load posts");

    const posts = await res.json();
    postsContainer.innerHTML = "";

    posts.forEach(post => {
      const div = document.createElement("div");
      div.className = "card post";
      div.id = `post-${post._id}`;

      // State for Like
      const isLiked = post.isLiked;
      const likeCount = post.likeCount || 0;
      const commentCount = post.commentCount || 0;

      div.innerHTML = `
        <div class="post-top">
          <div class="post-profile-wrap">
            <img src="${post.author_pfp || '/static/images/avatar_3d.png'}" class="post-pfp" />
            <div class="post-info">
              <span class="post-user">${post.username || 'User'}</span>
              <span class="post-time">${timeAgo(post.created_at || post.createdAt)}</span>
            </div>
          </div>
          <div class="post-header-actions">
              <button class="add-network-btn">Add Network <i class="fas fa-plus-circle"></i></button>
              <div class="post-menu">
                <span class="dots">⋮</span>
                <div class="menu-dropdown">
                  <div class="menu-item delete">🗑 Delete</div>
                </div>
              </div>
          </div>
        </div>

        ${post.content ? `<p class="post-content-text">${post.content}</p>` : ''}
        
        <div class="post-media-container">
          ${post.media && post.media.length > 0 ? post.media.map(item =>
        item.type === "video"
          ? `<video src="${item.url}" controls class="post-media-item"></video>`
          : `<img src="${item.url}" class="post-media-item" onerror="this.style.display='none'" />`
      ).join('') : ""}
        </div>

        <div class="post-actions-bar">
           <div class="left-actions">
               <div class="action-item like-action ${isLiked ? 'liked' : ''}" data-id="${post._id}">
                 <i class="${isLiked ? 'fas' : 'far'} fa-heart" style="${isLiked ? 'color: #e53e3e;' : ''}"></i> 
                 <span class="action-count">${likeCount > 0 ? likeCount : ''}</span>
               </div>
               <div class="action-item comment-action" data-id="${post._id}">
                 <i class="far fa-comment"></i> 
                 <span class="action-count">${commentCount > 0 ? commentCount : ''}</span>
               </div>
               <div class="action-item share-action" data-id="${post._id}">
                 <i class="far fa-paper-plane"></i> 
                 <span class="action-count"></span>
               </div>
           </div>
           <div class="right-actions">
               <div class="action-item save-action">
                 <i class="far fa-bookmark"></i>
               </div>
           </div>
        </div>

        <!-- Persistent Footer for Comment Input -->
        <div class="post-footer">
            <img src="/static/images/avatar_3d.png" class="footer-avatar" /> <!-- Current User Avatar -->
            <div class="footer-input-wrap">
                <input type="text" class="footer-comment-input" placeholder="Write Your Comment..." />
            </div>
        </div>

        <!-- Existing Comments Section (Hidden by default) -->
        <div class="comments-section" id="comments-${post._id}" style="display: none;">
            <div class="existing-comments">
                ${(post.comments || []).map(c => `
                    <div class="comment-item">
                        <strong>${c.username || 'User'}</strong>: ${c.text}
                    </div>
                `).join('')}
            </div>
        </div>
      `;

      // --- EVENT LISTENERS ---

      // 1. Menu Toggle
      const dots = div.querySelector(".dots");
      const menu = div.querySelector(".menu-dropdown");
      if (dots && menu) {
        dots.onclick = (e) => {
          e.stopPropagation();
          // Close all other menus first
          document.querySelectorAll('.menu-dropdown').forEach(m => {
            if (m !== menu) m.style.display = 'none';
          });
          menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
        };
      }

      // 2. Delete Post
      const delBtn = div.querySelector(".delete");
      if (delBtn) {
        delBtn.onclick = async () => {
          if (confirm("Delete post?")) {
            await fetch(`/api/posts/${post._id || post.id}`, { method: 'DELETE' });
            div.remove(); // Optimistic removal
          }
        };
      }

      // 3. Like Action
      const likeBtn = div.querySelector(".like-action");
      if (likeBtn) {
        likeBtn.onclick = () => toggleLike(post._id, likeBtn);
      }

      // 4. Comment Toggle (Show hidden existing comments)
      const commentBtn = div.querySelector(".comment-action");
      const commentsSection = div.querySelector(`#comments-${post._id}`);
      if (commentBtn && commentsSection) {
        commentBtn.onclick = () => {
          const isHidden = commentsSection.style.display === "none";
          commentsSection.style.display = isHidden ? "block" : "none";
        };
      }

      // 5. Submit Comment (Persistent Footer Input)
      const footerInput = div.querySelector(".footer-comment-input");
      const existingCommentsDiv = div.querySelector(".existing-comments");

      if (footerInput) {
        footerInput.addEventListener("keydown", (e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            submitComment(post._id, footerInput, existingCommentsDiv, div.querySelector('.action-count')); // Note: selector might need adjustment if multiple action-counts exist, usually first or search specifically
          }
        });
      }

      // 6. Share Action
      const shareBtn = div.querySelector(".share-action");
      if (shareBtn) {
        shareBtn.onclick = () => sharePost(post._id);
      }

      postsContainer.appendChild(div);
    });

  } catch (err) {
    console.error("Load Error:", err);
  }
}

async function toggleLike(postId, btn) {
  const icon = btn.querySelector("i");
  const countSpan = btn.querySelector(".action-count"); // Updated class
  let currentCount = parseInt(countSpan.innerText) || 0;

  // Optimistic UI Update
  const isLiked = btn.classList.contains("liked");

  if (isLiked) {
    // Un-like
    btn.classList.remove("liked");
    icon.classList.replace("fas", "far");
    icon.style.color = "";
    currentCount = Math.max(0, currentCount - 1);
  } else {
    // Like
    btn.classList.add("liked");
    icon.classList.replace("far", "fas");
    icon.style.color = "#e53e3e";
    currentCount++;
  }

  // Update text (empty if 0)
  countSpan.innerText = currentCount > 0 ? currentCount : "";

  try {
    const res = await fetch(`/api/posts/${postId}/like`, { method: "PUT" });
    if (!res.ok) throw new Error("Failed to like");
  } catch (err) {
    console.error("Like failed:", err);
    // Revert
    if (isLiked) {
      btn.classList.add("liked");
      icon.classList.replace("far", "fas");
      icon.style.color = "#e53e3e";
      countSpan.innerText = currentCount + 1;
    } else {
      btn.classList.remove("liked");
      icon.classList.replace("fas", "far");
      icon.style.color = "";
      countSpan.innerText = currentCount > 0 ? currentCount - 1 : "";
    }
  }
}

async function submitComment(postId, input, container, countSpan) {
  const text = input.value.trim();
  if (!text) return;

  try {
    const res = await fetch(`/api/posts/${postId}/comment`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });

    if (!res.ok) throw new Error("Failed to comment");

    const comments = await res.json();
    const newComment = comments[comments.length - 1];

    const commentDiv = document.createElement("div");
    commentDiv.className = "comment-item"; // New class
    commentDiv.innerHTML = `<strong>${newComment.username || 'Me'}</strong>: ${newComment.text}`;
    container.appendChild(commentDiv);

    input.value = "";

    // Update count
    let currentCount = parseInt(countSpan.innerText) || 0;
    countSpan.innerText = currentCount + 1;

  } catch (err) {
    console.error("Comment failed:", err);
    alert("Failed to post comment");
  }
}

async function sharePost(postId) {
  const url = `${window.location.origin}/?post=${postId}`; // Hypothetical deep link
  try {
    await navigator.clipboard.writeText(url);
    alert("Link copied to clipboard!");
  } catch (err) {
    // Fallback
    const textArea = document.createElement("textarea");
    textArea.value = url;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand("copy");
    document.body.removeChild(textArea);
    alert("Link copied to clipboard!");
  }
}

