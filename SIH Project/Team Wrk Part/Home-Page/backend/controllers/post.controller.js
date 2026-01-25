const Post = require("../models/Post");

exports.getPosts = async (req, res) => {
  try {
    const posts = await Post.find().sort({ createdAt: -1 });
    res.json(posts);
  } catch (err) {
    console.error("GET POSTS ERROR:", err);
    res.status(500).json({ message: "Failed to load posts" });
  }
};

exports.createPost = async (req, res) => {
  try {
    const { content } = req.body;

    console.log("REQ.FILES:", req.files);

    if (!content && (!req.files || req.files.length === 0)) {
      return res.status(400).json({ message: "Post content or media required" });
    }

    const postData = {
      content: content || "",
      user: req.user.id,
      media: []
    };

    if (req.files && req.files.length > 0) {
      req.files.forEach(file => {
        const mediaUrl = `${req.protocol}://${req.get("host")}/uploads/${file.filename}`;
        const mediaType = file.mimetype.startsWith("video") ? "video" : "image";
        postData.media.push({ url: mediaUrl, type: mediaType });
      });
    }

    const post = await Post.create(postData);

    res.status(201).json(post);
  } catch (err) {
    console.error("CREATE POST ERROR:", err);
    res.status(500).json({
      message: "Post creation failed",
      error: err.message
    });
  }
};
// LIKE / UNLIKE
exports.toggleLike = async (req, res) => {
  try {
    const post = await Post.findById(req.params.id);
    if (!post) return res.status(404).json({ message: "Post not found" });

    const userId = req.user.id;

    if (post.likes.includes(userId)) {
      post.likes.pull(userId); // UNLIKE
    } else {
      post.likes.push(userId); // LIKE
    }

    await post.save();
    res.json({ likes: post.likes.length });

  } catch (err) {
    console.error(err);
    res.status(500).json({ message: "Like failed" });
  }
};

// COMMENT
exports.addComment = async (req, res) => {
  try {
    const { text } = req.body;
    if (!text) return res.status(400).json({ message: "Comment required" });

    const post = await Post.findById(req.params.id);
    if (!post) return res.status(404).json({ message: "Post not found" });

    post.comments.push({
      user: req.user.id,
      text
    });

    await post.save();
    res.status(201).json(post.comments);

  } catch (err) {
    console.error(err);
    res.status(500).json({ message: "Comment failed" });
  }
};

// DELETE POST
exports.deletePost = async (req, res) => {
  try {
    const post = await Post.findById(req.params.id);
    if (!post) return res.status(404).json({ message: "Post not found" });

    // Check if user owns the post
    if (post.user.toString() !== req.user.id) {
      return res.status(401).json({ message: "Not authorized" });
    }

    await post.deleteOne();
    res.json({ message: "Post deleted" });
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: "Delete failed" });
  }
};

// UPDATE POST
exports.updatePost = async (req, res) => {
  try {
    const { content } = req.body;
    const post = await Post.findById(req.params.id);

    if (!post) return res.status(404).json({ message: "Post not found" });

    if (post.user.toString() !== req.user.id) {
      return res.status(401).json({ message: "Not authorized" });
    }

    post.content = content || post.content;
    await post.save();
    res.json(post);
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: "Update failed" });
  }
};
