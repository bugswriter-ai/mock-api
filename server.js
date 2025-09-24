// server.js
import express from "express";
import { MongoClient, ObjectId } from "mongodb";
import bodyParser from "body-parser";
import cors from "cors";
import dotenv from "dotenv";

dotenv.config(); // load .env variables

const app = express();
app.use(cors());
app.use(bodyParser.json());

const uri = process.env.MONGODB_URI;  // ✅ read from .env
const client = new MongoClient(uri);

let db;

async function connectDB() {
  await client.connect();
  db = client.db("test"); // database
  console.log("✅ Connected to MongoDB");
}

app.post("/update-coordinates", async (req, res) => {
  try {
    const { id, coordinates } = req.body;
    if (!id || !coordinates) {
      return res.status(400).json({ error: "Missing id or coordinates" });
    }

    const result = await db.collection("ner_results").updateOne(
      { _id: new ObjectId(id) },
      { $set: { "entities.coordinates": coordinates } },
      { upsert: false } // set true if you want insert when not found
    );

    res.json({ success: true, matched: result.matchedCount, modified: result.modifiedCount });
  } catch (err) {
    console.error("❌ Error updating:", err);
    res.status(500).json({ error: "Server error" });
  }
});

const PORT = process.env.PORT || 4000;
connectDB().then(() => {
  app.listen(PORT, () => console.log(`🚀 Server running on http://localhost:${PORT}`));
});
