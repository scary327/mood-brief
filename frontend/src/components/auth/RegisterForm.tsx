"use client";

import { useState } from "react";
import { Card, Input, Button, Alert } from "antd";
import {
  EyeInvisibleOutlined,
  EyeOutlined,
  UserOutlined,
  MailOutlined,
  LockOutlined,
  CheckCircleOutlined,
} from "@ant-design/icons";
import Link from "next/link";
import { registerUser } from "@/app/auth/actions";

const PASSWORD_MIN_LENGTH = 8;

interface PasswordStrength {
  hasLetter: boolean;
  hasDigit: boolean;
  isLongEnough: boolean;
}

function getPasswordStrength(password: string): PasswordStrength {
  return {
    hasLetter: /[a-zA-Z]/.test(password),
    hasDigit: /[0-9]/.test(password),
    isLongEnough: password.length >= PASSWORD_MIN_LENGTH,
  };
}

function isPasswordValid(strength: PasswordStrength): boolean {
  return strength.hasLetter && strength.hasDigit && strength.isLongEnough;
}

export default function RegisterForm() {
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordStrength, setPasswordStrength] = useState<PasswordStrength>({
    hasLetter: false,
    hasDigit: false,
    isLongEnough: false,
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const pwd = e.target.value;
    setPassword(pwd);
    setPasswordStrength(getPasswordStrength(pwd));
  };

  const handleConfirmPasswordChange = (
    e: React.ChangeEvent<HTMLInputElement>,
  ) => {
    setConfirmPassword(e.target.value);
  };

  const passwordsMatch = password === confirmPassword;
  const isFormValid = isPasswordValid(passwordStrength) && passwordsMatch;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isFormValid) return;

    setIsLoading(true);
    setError("");

    const res = await registerUser(email, username, password);
    if (res.success) {
      window.location.href = "/";
    } else {
      setError(res.error || "Неизвестная ошибка регистрации");
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
          Создать аккаунт
        </h1>
        <p className="text-[#71717a] m-0">
          Зарегистрируйтесь, чтобы начать работу
        </p>
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
            Username
          </label>
          <Input
            name="username_ignore_autofill"
            placeholder="Ваше имя"
            prefix={<UserOutlined />}
            size="large"
            disabled={isLoading}
            required
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-[#52525b] mb-2">
            Пароль
          </label>
          <Input.Password
            name="password_ignore_autofill"
            placeholder="Минимум 8 символов, буквы и цифры"
            prefix={<LockOutlined />}
            size="large"
            disabled={isLoading}
            value={password}
            onChange={handlePasswordChange}
            iconRender={(visible) =>
              visible ? <EyeOutlined /> : <EyeInvisibleOutlined />
            }
            required
          />

          {password && (
            <div className="mt-3 space-y-1 text-sm">
              <div
                className={`flex items-center gap-2 ${
                  passwordStrength.hasLetter
                    ? "text-green-600"
                    : "text-gray-500"
                }`}
              >
                {passwordStrength.hasLetter && <CheckCircleOutlined />}
                <span>Буквы</span>
              </div>
              <div
                className={`flex items-center gap-2 ${
                  passwordStrength.hasDigit ? "text-green-600" : "text-gray-500"
                }`}
              >
                {passwordStrength.hasDigit && <CheckCircleOutlined />}
                <span>Цифры</span>
              </div>
              <div
                className={`flex items-center gap-2 ${
                  passwordStrength.isLongEnough
                    ? "text-green-600"
                    : "text-gray-500"
                }`}
              >
                {passwordStrength.isLongEnough && <CheckCircleOutlined />}
                <span>Минимум 8 символов</span>
              </div>
            </div>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-[#52525b] mb-2">
            Подтвердить пароль
          </label>
          <Input.Password
            name="confirmPassword_ignore_autofill"
            placeholder="Повторите пароль"
            prefix={<LockOutlined />}
            size="large"
            disabled={isLoading}
            value={confirmPassword}
            onChange={handleConfirmPasswordChange}
            iconRender={(visible) =>
              visible ? <EyeOutlined /> : <EyeInvisibleOutlined />
            }
            required
          />
          {password && confirmPassword && !passwordsMatch && (
            <div className="mt-2 text-sm text-red-600">Пароли не совпадают</div>
          )}
        </div>

        <Button
          type="primary"
          htmlType="submit"
          block
          size="large"
          loading={isLoading}
          disabled={isLoading || !isFormValid}
        >
          Зарегистрироваться
        </Button>
      </form>

      <div className="mt-4 text-center">
        <span className="text-[#71717a]">Уже есть аккаунт? </span>
        <Link href="/auth/login" className="text-blue-500 hover:text-blue-600">
          Войти
        </Link>
      </div>
    </Card>
  );
}
