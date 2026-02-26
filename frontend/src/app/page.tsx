"use client";

import { Button, Card, Space, Divider } from "antd";
import {
  ArrowRightOutlined,
  BulbOutlined,
  RobotOutlined,
  EditOutlined,
  CheckCircleOutlined,
  AppstoreAddOutlined,
} from "@ant-design/icons";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  return (
    <div className="container">
      {/* Hero Section */}
      <section className="text-center mt-10 px-5 py-10">
        <h1 className="text-[4rem] font-extrabold mb-6 bg-gradient-to-r from-[#1d1d1f] to-[#7d7d85] bg-clip-text text-transparent tracking-[-0.04em] leading-tight">
          MoodBrief
        </h1>
        <p className="text-[1.4rem] font-medium text-[#4b4b53] max-w-[800px] mx-auto mb-10 leading-relaxed">
          Сервис оформления визуальных предпочтений клиента в структурированное
          техническое задание
        </p>
        <Space size="middle">
          <Button
            type="primary"
            size="large"
            shape="round"
            icon={<ArrowRightOutlined />}
            className="!h-14 !px-10 !text-[1.1rem] !bg-[#1d1d1f] !border-[#1d1d1f] !shadow-[0_8px_24px_rgba(29,29,31,0.2)]"
            onClick={() => router.push("/moodboard")}
          >
            Начать проект
          </Button>
          <Button
            size="large"
            shape="round"
            icon={<AppstoreAddOutlined />}
            className="!h-14 !px-10 !text-[1.1rem] !bg-white/50 !border-transparent"
            onClick={() => router.push("/dashboard")}
          >
            Дашборд
          </Button>
        </Space>
      </section>

      <Divider className="!border-black/6" />

      {/* Описание сервиса */}
      <section>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-2xl font-bold tracking-[-0.02em] mb-4">
              От визуала к чёткому ТЗ
            </h2>
            <p className="text-[1.1rem] text-[#4b4b53] leading-[1.8] mb-4">
              <b>MoodBrief</b> — это современный веб-сервис, предназначенный для
              преобразования визуальных предпочтений клиента в строго
              структурированное техническое задание для дизайн‑ или проектной
              команды.
            </p>
            <p className="text-[1.1rem] text-[#4b4b53] leading-[1.8]">
              Сервис реализует пошаговый процесс: от выбора типа задачи
              (логотип, сайт, архитектура, благоустройство) и оценки примеров,
              до автоматического формирования moodboard&apos;а и генерации
              текстового описания с указанием стиля, палитры и ограничений.
            </p>
          </div>
          <Card variant="borderless" className="!rounded-3xl !p-6">
            <div className="flex flex-col gap-6 w-full">
              <div>
                <div className="flex items-center gap-4 mb-2">
                  <div className="bg-blue-500/10 p-3 rounded-xl flex items-center justify-center">
                    <RobotOutlined className="text-blue-500 text-2xl" />
                  </div>
                  <h4 className="text-lg font-semibold m-0">Умная генерация</h4>
                </div>
                <p className="text-base text-gray-500 mt-1">
                  Автоматический сбор moodboard&apos;а и текстового описания на
                  основе скрытых описаний ваших предпочтений.
                </p>
              </div>
              <Divider className="!my-0 !border-black/4" />
              <div>
                <div className="flex items-center gap-4 mb-2">
                  <div className="bg-orange-500/10 p-3 rounded-xl flex items-center justify-center">
                    <EditOutlined className="text-orange-500 text-2xl" />
                  </div>
                  <h4 className="text-lg font-semibold m-0">
                    Прозрачное редактирование
                  </h4>
                </div>
                <p className="text-base text-gray-500 mt-1">
                  Пользователь получает черновик ТЗ, который он может
                  отредактировать перед финальным утверждением.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </section>

      {/* Ожидаемый эффект */}
      <section className="pt-10">
        <h2 className="text-2xl font-bold text-center mb-10">
          Ожидаемый эффект
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card
            hoverable
            variant="borderless"
            className="!h-full !rounded-3xl !p-4 !bg-white/30"
          >
            <BulbOutlined className="text-[2.5rem] text-pink-500 mb-5 block" />
            <h4 className="text-lg font-semibold mb-2">
              Визуальное анкетирование
            </h4>
            <p className="text-[#4b4b53] leading-relaxed">
              Заказчик выбирает изображения интуитивно, а система работает с их
              скрытыми описаниями. Человек оценивает визуал, а алгоритм
              структурирует данные для точного подбора стиля.
            </p>
          </Card>
          <Card
            hoverable
            variant="borderless"
            className="!h-full !rounded-3xl !p-4 !bg-white/30"
          >
            <RobotOutlined className="text-[2.5rem] text-green-500 mb-5 block" />
            <h4 className="text-lg font-semibold mb-2">Снятие рутины</h4>
            <p className="text-[#4b4b53] leading-relaxed">
              Автоматическая генерация moodboard&apos;а и черновика снимает с
              дизайнера рутину сбора материалов, освобождая драгоценное время
              для по-настоящему творческих задач.
            </p>
          </Card>
          <Card
            hoverable
            variant="borderless"
            className="!h-full !rounded-3xl !p-4 !bg-white/30"
          >
            <CheckCircleOutlined className="text-[2.5rem] text-blue-500 mb-5 block" />
            <h4 className="text-lg font-semibold mb-2">
              Точность и Прозрачность
            </h4>
            <p className="text-[#4b4b53] leading-relaxed">
              Возможность правки обеспечения ТЗ заказчиком дает прозрачность
              требований до начала разработки. <b>Результат:</b> сокращение
              цикла согласования и минимум правок на старте.
            </p>
          </Card>
        </div>
      </section>

      <section className="text-center py-20 pb-10">
        <h3 className="text-xl font-semibold mb-4">
          Готовы автоматизировать рутину?
        </h3>
        <p className="text-[1.15rem] text-[#4b4b53] mb-10">
          Используйте MoodBrief для оптимизации предпроектной подготовки уже
          сегодня.
        </p>
        <Button
          size="large"
          type="default"
          shape="round"
          className="!h-[50px] !px-10 !font-medium !bg-white/70"
          onClick={() => router.push("/moodboard")}
        >
          Создать ТЗ
        </Button>
      </section>
    </div>
  );
}
