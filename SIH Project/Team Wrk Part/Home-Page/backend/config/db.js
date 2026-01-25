const mongoose = require("mongoose");

const connectDB = async () => {
  try {
    await mongoose.connect(
      "mongodb+srv://mubeenunnisajaids2024_db_user:Reshma1234@cluster0.g1xjlvw.mongodb.net/?appName=Cluster0"
    );

    console.log("MongoDB connected successfully ");
  } catch (error) {
    console.error("MongoDB connection failed ");
    console.error(error.message);
    process.exit(1);
  }
};

module.exports = connectDB;
