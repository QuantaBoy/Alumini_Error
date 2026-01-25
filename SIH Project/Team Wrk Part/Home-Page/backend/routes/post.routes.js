const express = require("express");
const router = express.Router();
const upload = require("../middleware/upload");
const auth = require("../middleware/auth.middleware");
const postController = require("../controllers/post.controller");

router.get("/", postController.getPosts);

router.post(
  "/",
  auth,
  upload.array("files", 10),
  postController.createPost
);

//  NEW
router.put("/:id/like", auth, postController.toggleLike);
router.post("/:id/comment", auth, postController.addComment);
router.delete("/:id", auth, postController.deletePost);
router.put("/:id", auth, postController.updatePost);

module.exports = router;
