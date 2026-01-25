const jwt = require("jsonwebtoken");

module.exports = (req, res, next) => {
  const authHeader = req.headers.authorization;

  console.log("AUTH HEADER:", authHeader);

  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return res.status(401).json({
      success: false,
      message: "Authorization token missing"
    });
  }

  const token = authHeader.split(" ")[1];

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    // decoded must contain id
    if (!decoded.id) {
      return res.status(401).json({
        success: false,
        message: "Invalid token payload"
      });
    }

    req.user = decoded;
    next();

  } catch (err) {
    console.error("JWT ERROR:", err.message);

    return res.status(401).json({
      success: false,
      message: err.name === "TokenExpiredError"
        ? "Token expired. Please login again."
        : "Invalid token"
    });
  }
};
