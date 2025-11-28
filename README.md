# 🏋️ Training Tracker — Backend (FastAPI)

本專案為 [Training Tracker]((https://github.com/Latseng/training-next)) Web App 的後端 Server。使用 FastAPI + Supabase Auth + Supabase Database 建構。

後端負責使用者驗證、訓練資料 CRUD、訓練分析邏輯，以及串接 Gemini API 作為 AI 訓練教練。

本後端完整支援[前端](https://github.com/Latseng/training-next) 使用的所有 API，並採用 Cookie-based Token Transport 提升安全性。

## ✨ Features
🔐 Authentication（Supabase Auth + HttpOnly Cookies）

Email/Password 登入

使用 Supabase 進行 Token 驗證

Access Token 與 Refresh Token 儲存在 HttpOnly Cookie

自動解析 Cookie 中的 access_token

受保護路由再次驗證（get_current_user）請求使用者身份

## 🏋️ 訓練紀錄（Strength Training Records）

訓練課程（主題、目標）路由CRUD

建立課程底下的多個訓練項目

記錄每個項目的訓練量（重量、組數、反覆次數）

Supabase 資料庫 CRUD

## 📊 訓練分析（Training Analysis）

接收使用者選擇的日期區間

查詢 Supabase 中的訓練紀錄

前端會將折線圖（Recharts）可視化

## 🤖 AI 教練（Gemini API）

FastAPI 呼叫 Google Gemini API

傳入使用者的訓練紀錄

AI 回傳分析與改善建議

前端以 Chat UI 呈現