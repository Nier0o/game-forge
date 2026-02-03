import AppError from '../utils/appError.js';

const handleCastErrorDB = (err) => {
    const message = `Invalid ${err.path}: ${err.value}.`;
    return new AppError(message, 400);
};

const handleDuplicateFieldsDB = (err) => {
    const value = err.keyValue
        ? JSON.stringify(err.keyValue)
        : 'duplicate value';
    const message = `Duplicate field value: ${value}. Please use another value!`;
    return new AppError(message, 400);
};

const handleValidationErrorDB = (err) => {
    const errors = Object.values(err.errors).map((el) => el.message);
    const message = `Invalid input data.${errors.join('. ')}`;
    return new AppError(message, 400);
};

const handleJWTError = (err) => {
    const message = `Invalid token. Please log in again!`;
    return new AppError(message, 401);
};

const handleTokenExpiredError = (err) => {
    const message = `Your token has expired! Please log in again.`;
    return new AppError(message, 401);
};

const sendDevError = (err, res) => {
    res.status(err.statusCode).json({
        status: err.status,
        err: err,
        message: err.message,
        stack: err.stack,
    });
};

const sendProdError = (err, res) => {
    if (err.isOperational) {
        res.status(err.statusCode).json({
            status: err.status,
            message: err.message,
        });
    } else {
        console.error('Error 💥', err);
        res.status(500).json({
            status: 'error',
            message: 'Something went very wrong!',
        });
    }
};

export default (err, req, res, next) => {
    err.statusCode = err.statusCode || 500;
    err.status = err.status || 'error';

    if (process.env.NODE_ENV === 'development') {
        sendDevError(err, res);
    } else if (process.env.NODE_ENV === 'production') {
        if (err.name === 'CastError') {
            err = handleCastErrorDB(err);
        }

        if (err.code === 11000) {
            err = handleDuplicateFieldsDB(err);
        }

        if (err.name === 'ValidationError') {
            err = handleValidationErrorDB(err);
        }

        if (err.name === 'JsonWebTokenError') {
            err = handleJWTError(err);
        }

        if (err.name === 'TokenExpiredError') {
            err = handleTokenExpiredError(err);
        }

        sendProdError(err, res);
    }
};