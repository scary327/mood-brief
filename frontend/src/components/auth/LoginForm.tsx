"use client";

import { useState } from "react";
import { Card, Input, Button, Alert } from "antd";
import {
  MailOutlined,
  LockOutlined,
  EyeInvisibleOutlined,
  EyeOutlined,
} from "@ant-design/icons";
import Link from "next/link";
import { loginUser } from "@/app/auth/actions";

export default function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    const res = await loginUser(email, password);
    if (res.success) {
      window.location.href = "/";
    } else {
      setError(res.error || "Неверный логин или пароль");
      setIsLoading(false);
    }
  };

  return (
    <Card
      className="shadow-lg border-0 rounded-lg"
      style={{ borderRadius: "12px" }}
    >
      <div className="text-center mb-6">
        <h1 className="text-2xl font-bold text-[#1d1d1f] m-0 mb-2">
          MoodBrief
        </h1>
        <p className="text-[#71717a] m-0">Входите в систему</p>
      </div>

      {error && (
        <Alert message={error} type="error" showIcon className="mb-4" />
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-[#52525b] mb-2">
            Email
          </label>
          <Input
            name="email_ignore_autofill"
            type="email"
            placeholder="your@email.com"
            prefix={<MailOutlined />}
            size="large"
            disabled={isLoading}
            autoFocus
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-[#52525b] mb-2">
            Пароль
          </label>
          <Input.Password
            name="password_ignore_autofill"
            placeholder="Введите пароль"
            prefix={<LockOutlined />}
            size="large"
            disabled={isLoading}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            iconRender={(visible) =>
              visible ? <EyeOutlined /> : <EyeInvisibleOutlined />
            }
            required
          />
        </div>

        <Button
          type="primary"
          htmlType="submit"
          block
          size="large"
          loading={isLoading}
          disabled={isLoading}
        >
          Войти
        </Button>
      </form>

      <div className="mt-4 text-center">
        <span className="text-[#71717a]">Нет аккаунта? </span>
        <Link
          href="/auth/register"
          className="text-blue-500 hover:text-blue-600"
        >
          Зарегистрируйтесь
        </Link>
      </div>
    </Card>
  );
}
