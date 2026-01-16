// generate_jwt.js
require('dotenv').config();
const jwt = require('jsonwebtoken');

// Read secret from .env
const secretKey = process.env.JWT_SECRET_KEY;
if (!secretKey) {
  console.error("❌ No JWT_SECRET_KEY found in .env");
  process.exit(1);
}

// Define payload
const payload = {
  userId: 123,
  role: "lawyer",
  iat: Math.floor(Date.now() / 1000),                  // issued at
  exp: Math.floor(Date.now() / 1000) + (60 * 60)       // expires in 1 hour
};

// Generate token
const token = jwt.sign(payload, secretKey, { algorithm: 'HS256' });

// Output
console.log("✅ JWT generated:");
console.log(token);