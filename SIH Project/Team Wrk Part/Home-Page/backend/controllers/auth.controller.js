const User = require("../models/User");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");

/* =========================
   SIGNUP CONTROLLER
========================= */
exports.signup = async (req, res) => {
  try {
    const { username, email, password } = req.body;

    //  Validate input
    if (!username || !email || !password) {
      return res.status(400).json({
        message: "All fields (username, email, password) are required"
      });
    }

    //   Check existing user
    const existingUser = await User.findOne({
      $or: [{ email }, { username }]
    });

    if (existingUser) {
      return res.status(400).json({
        message: "User already exists"
      });
    }

    //  Hash password
    const hashedPassword = await bcrypt.hash(password, 10);

    //   Create user
    const user = await User.create({
      username,
      email,
      password: hashedPassword
    });

    //   Success response
    res.status(201).json({
      message: "User created successfully",
      user: {
        id: user._id,
        username: user.username,
        email: user.email
      }
    });

  } catch (err) {
    //  VERY IMPORTANT: show real error
    console.error(" SIGNUP ERROR:", err);

    res.status(500).json({
      message: "Signup failed",
      error: err.message
    });
  }
};

/* =========================
   LOGIN CONTROLLER
========================= */
exports.login = async (req, res) => {
  try {
    const { email, password } = req.body;

    //   Validate input
    if (!email || !password) {
      return res.status(400).json({
        message: "Email and password are required"
      });
    }

    //   Find user
    const user = await User.findOne({ email });
    if (!user) {
      return res.status(400).json({
        message: "User not found"
      });
    }

    //   Compare password
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(400).json({
        message: "Invalid password"
      });
    }

    //   Create JWT
    const token = jwt.sign(
      { id: user._id },
      process.env.JWT_SECRET,
      { expiresIn: "30d" }
    );

    //   Success response
    res.status(200).json({
      token,
      user: {
        id: user._id,
        username: user.username,
        email: user.email
      }
    });

  } catch (err) {
    console.error(" LOGIN ERROR:", err);

    res.status(500).json({
      message: "Login failed",
      error: err.message
    });
  }
};
