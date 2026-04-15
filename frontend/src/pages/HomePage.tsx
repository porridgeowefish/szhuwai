import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { HeroSection } from '../components/HeroSection';
import { PlanData } from '../types';

export interface TouchedFields {
  tripDate: boolean;
  departurePoint: boolean;
  planTitle: boolean;
  destination1: boolean;
  file: boolean;
}

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [tripDate, setTripDate] = useState('');
  const [departurePoint, setDeparturePoint] = useState('');
  const [additionalInfo, setAdditionalInfo] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [plan, setPlan] = useState<PlanData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fileFormatError, setFileFormatError] = useState<string | null>(null);

  // 线路名称和核心目的地
  const [planTitle, setPlanTitle] = useState('');
  const [destination1, setDestination1] = useState('');
  const [destination2, setDestination2] = useState('');
  const [destination3, setDestination3] = useState('');

  // 实时验证：touched 追踪
  const [touched, setTouched] = useState<TouchedFields>({
    tripDate: false,
    departurePoint: false,
    planTitle: false,
    destination1: false,
    file: false,
  });

  const markTouched = (field: keyof TouchedFields) => {
    setTouched(prev => ({ ...prev, [field]: true }));
  };

  // 验证结果
  const validation = useMemo(() => {
    const destinations = [destination1, destination2, destination3].filter(d => d.trim());
    return {
      tripDate: tripDate.trim() !== '',
      departurePoint: departurePoint.trim() !== '',
      planTitle: planTitle.trim() !== '',
      destination: destinations.length > 0,
      file: file !== null,
    };
  }, [tripDate, departurePoint, planTitle, destination1, destination2, destination3, file]);

  const isValid = Object.values(validation).every(Boolean);

  // 缺少字段的提示信息
  const missingHint = useMemo(() => {
    if (isValid) return null;
    const missing: string[] = [];
    if (!validation.tripDate) missing.push('出行日期');
    if (!validation.departurePoint) missing.push('出发地点');
    if (!validation.planTitle) missing.push('线路名称');
    if (!validation.destination) missing.push('至少一个核心目的地');
    if (!validation.file) missing.push('轨迹文件');
    return `还需填写：${missing.join('、')}`;
  }, [isValid, validation]);

  const handleTripDateChange = (v: string) => {
    setTripDate(v);
    markTouched('tripDate');
    setError(null);
  };

  const handleDeparturePointChange = (v: string) => {
    setDeparturePoint(v);
    markTouched('departurePoint');
    setError(null);
  };

  const handlePlanTitleChange = (v: string) => {
    setPlanTitle(v);
    markTouched('planTitle');
    setError(null);
  };

  const handleDestination1Change = (v: string) => {
    setDestination1(v);
    markTouched('destination1');
    setError(null);
  };

  const handleDestination2Change = (v: string) => {
    setDestination2(v);
    setError(null);
  };

  const handleDestination3Change = (v: string) => {
    setDestination3(v);
    setError(null);
  };

  const handleAdditionalInfoChange = (v: string) => {
    setAdditionalInfo(v);
  };

  const handleFileChange = (f: File | null) => {
    setFile(f);
    setFileFormatError(null);
    if (f) {
      markTouched('file');
    }
    setError(null);
  };

  const handleGenerate = async () => {
    // 标记所有字段为 touched
    setTouched({
      tripDate: true,
      departurePoint: true,
      planTitle: true,
      destination1: true,
      file: true,
    });

    if (!isValid) {
      setError(missingHint || '请完善表单信息');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const destinations = [destination1, destination2, destination3].filter(d => d.trim());
      const formData = new FormData();
      formData.append('trip_date', tripDate);
      formData.append('departure_point', departurePoint);
      formData.append('additional_info', additionalInfo);
      formData.append('file', file!);
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

  // 显示 Hero 入口页
  return (
    <div className="min-h-screen bg-[var(--sand)]">
      <HeroSection
        tripDate={tripDate}
        setTripDate={handleTripDateChange}
        departurePoint={departurePoint}
        setDeparturePoint={handleDeparturePointChange}
        planTitle={planTitle}
        setPlanTitle={handlePlanTitleChange}
        destination1={destination1}
        setDestination1={handleDestination1Change}
        destination2={destination2}
        setDestination2={handleDestination2Change}
        destination3={destination3}
        setDestination3={handleDestination3Change}
        additionalInfo={additionalInfo}
        setAdditionalInfo={handleAdditionalInfoChange}
        file={file}
        setFile={handleFileChange}
        isLoading={isLoading}
        onGenerate={handleGenerate}
        error={error}
        fileFormatError={fileFormatError}
        setFileFormatError={setFileFormatError}
        touched={touched}
        validation={validation}
        isValid={isValid}
        missingHint={missingHint}
      />
    </div>
  );
};

export default HomePage;
