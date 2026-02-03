// test comment
import express from 'express';
import helmet from 'helmet';
import morgan from 'morgan';
import rateLimit from 'express-rate-limit';
import mongoSanitize from 'express-mongo-sanitize';
import xss from 'xss-clean';
import AppError from './utils/appError.js';
import errorController from './controllers/errorController.js';
const app = express();
app.use(helmet());

if (process.env.NODE_ENV === 'development') {
    app.use(morgan('dev'));
}

const limiter = rateLimit({
    max: 100,
    windowMs: 60 * 60 * 1000,
    message: 'Too many requests from this IP, please try again in an hour!',
});
app.use('/api', limiter);

app.use(express.json({ limit: '10kb' }));

app.use(mongoSanitize());

app.use(xss());

// Serving static files
// app.use(express.static(`${__dirname}/public`));

app.get('/api/health', (req, res) => {
  res.status(200).json({ status: 'success', message: 'Backend is reachable!' });
});

app.get('/api/hello', (req, res) => {
  res.status(200).json({ message: 'Hello from GameForge Backend!' });
});

app.all('*', (req, res, next) => {
    next(new AppError(`Can't find ${req.originalUrl} on this server!`, 404)); // Middleware: handles undefined routes
});

app.use(errorController);

export default app;