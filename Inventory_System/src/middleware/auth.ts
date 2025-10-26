import { Request, Response, NextFunction } from 'express';

export default function auth(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization || '';
  const token = authHeader.replace('Bearer ', '');
  if (!token || token !== process.env.SERVICE_TOKEN) {
    return res.status(401).json({ error: 'unauthorized' });
  }
  next();
}
