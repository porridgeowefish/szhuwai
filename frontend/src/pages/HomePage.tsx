import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { HeroSection } from '../components/HeroSection';
import { PlanData } from '../types';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [tripDate, setTripDate] = useState('');
  const [departurePoint, setDeparturePoint] = useState('');
  const [additionalInfo, setAdditionalInfo] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [plan, setPlan] = useState<PlanData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 线路名称和核心目的地
  const [planTitle, setPlanTitle] = useState('');
  const [destination1, setDestination1] = useState('');
  const [destination2, setDestination2] = useState('');
  const [destination3, setDestination3] = useState('');

  const handleGenerate = async () => {
    // 强拦截逻辑：校验必须字段
    if (!file || !tripDate || !departurePoint) {
      setError('必须选择日期、填写出发点并上传轨迹文件！');
      return;
    }

    if (!planTitle.trim()) {
      setError('请输入线路名称！');
      return;
    }

    const destinations = [destination1, destination2, destination3].filter(d => d.trim());
    if (destinations.length === 0) {
      setError('请至少填写一个核心目的地！');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('trip_date', tripDate);
      formData.append('departure_point', departurePoint);
      formData.append('additional_info', additionalInfo);
      formData.append('file', file);
      formData.append('plan_title', planTitle);
      formData.append('key_destinations', destinations.join(','));

      const response = await fetch('/api/v1/plan/generate', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`请求失败: ${response.status}`);
      }

      const responseData = await response.json();
      setPlan(responseData.data);

      // 生成成功后，跳转到报告详情页
      navigate(`/reports/${responseData.data.plan_id}`, { state: { plan: responseData.data } });
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成策划书失败，请稍后重试');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      const ext = selectedFile.name.split('.').pop()?.toLowerCase();
      if (ext === 'gpx' || ext === 'kml') {
        setFile(selectedFile);
      } else {
        setError('请选择 GPX 或 KML 格式的文件');
      }
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // 显示 Hero 入口页
  return (
    <div className="min-h-screen bg-[var(--sand)]">
      <HeroSection
        tripDate={tripDate}
        setTripDate={setTripDate}
        departurePoint={departurePoint}
        setDeparturePoint={setDeparturePoint}
        planTitle={planTitle}
        setPlanTitle={setPlanTitle}
        destination1={destination1}
        setDestination1={setDestination1}
        destination2={destination2}
        setDestination2={setDestination2}
        destination3={destination3}
        setDestination3={setDestination3}
        additionalInfo={additionalInfo}
        setAdditionalInfo={setAdditionalInfo}
        file={file}
        setFile={setFile}
        isLoading={isLoading}
        onGenerate={handleGenerate}
        error={error}
      />
    </div>
  );
};

export default HomePage;
