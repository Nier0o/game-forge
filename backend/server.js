import mongoose from 'mongoose';
import dotenv from 'dotenv';

process.on('unhandledRejection', (err) => {
	console.log('UNHANDLED REJECTION! Shutting down...');
	console.log(err.name, err.message);
	process.exit(1);
});

process.on('uncaughtException', (err) => {
	console.log('UNCAUGHT EXCEPTION! Shutting down...');
	console.log(err.name, err.message);
	process.exit(1);
});

dotenv.config({ path: './config.env' });
const app = require('./app');

const DB = process.env.DATABASE_LOCAL;
mongoose
	.connect(DB)
	.then((con) => {
		console.log('DB connection successful!');
	})
	.catch((err) => {
		console.log('DB connection error:', err);
	});

const port = process.env.PORT || 5000;
const server = app.listen(port, () => {
	console.log(`Server is running on http://localhost:${port}`);
});