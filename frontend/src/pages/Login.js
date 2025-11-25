import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API, useAuth } from '@/App';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { LogIn, Mail, Lock, Eye, EyeOff, Zap, Shield, TrendingUp } from 'lucide-react';
import { Globe } from '@/components/Globe';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [currentDisplay, setCurrentDisplay] = useState(0);
  const navigate = useNavigate();
  const { login } = useAuth();

  // Static branding
  const brand = { logo: 'B', name: 'BeaconIQ' };

  const features = [
    { text: 'AI-Powered Analytics', icon: Zap },
    { text: 'Enterprise Security', icon: Shield },
    { text: 'Real-Time Insights', icon: TrendingUp },
  ];

  // Create display items: logo, feature1, logo, feature2, logo, feature3
  const displayItems = [
    { type: 'logo' },
    { type: 'feature', ...features[0] },
    { type: 'logo' },
    { type: 'feature', ...features[1] },
    { type: 'logo' },
    { type: 'feature', ...features[2] },
  ];

  useEffect(() => {
    const displayInterval = setInterval(() => {
      setCurrentDisplay((prev) => (prev + 1) % displayItems.length);
    }, 3000); // Change every 3 seconds

    return () => clearInterval(displayInterval);
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      login(response.data.token, response.data.email);
      toast.success('Login successful!');
      navigate('/');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      className="min-h-screen flex relative"
      style={{ 
        backgroundImage: 'url(/login_bg.svg)',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat'
      }}
    >
      {/* Left Side - Globe */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        <div className="absolute inset-0 flex items-center justify-center" style={{ paddingTop: '80px' }}>
          {/* Globe container */}
          <div 
            className="relative flex items-center justify-center"
            style={{ 
              width: '550px', 
              height: '550px',
            }}
          >
            <Globe className="w-full h-full relative z-10" />
            
            {/* Features text or logo positioned just above globe */}
            <div 
              className="absolute z-20"
              style={{
                top: '-120px',
                left: '50%',
                transform: 'translateX(-50%)',
              }}
            >
              <div 
                key={currentDisplay}
                className="animate-fade-in flex items-center justify-center"
                style={{ minHeight: '144px' }}
              >
                {displayItems[currentDisplay].type === 'logo' ? (
                  <img 
                    src="/Vector-Logo-white.svg" 
                    alt="Vector AI Studio" 
                    className="h-36 w-auto"
                    style={{ display: 'block' }}
                  />
                ) : (
                  <div className="flex items-center justify-center gap-4 whitespace-nowrap">
                    {React.createElement(displayItems[currentDisplay].icon, { className: "w-8 h-8 text-white" })}
                    <p className="text-2xl font-bold text-white">{displayItems[currentDisplay].text}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
        {/* Small logo in bottom left */}
        <div className="absolute bottom-6 left-6 z-10">
          <div className="w-10 h-10 bg-white flex items-center justify-center">
            <span className="text-black font-bold text-lg">{brand.logo}</span>
          </div>
        </div>
      </div>

      {/* Right Side - Login Form */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center p-8">
        <div className="w-full max-w-md mx-auto">
          {/* Static Logo and Text at top */}
          <div className="mb-10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white flex items-center justify-center">
                <span className="text-black font-bold text-xl">{brand.logo}</span>
              </div>
              <h1 className="text-3xl font-bold text-white">{brand.name}</h1>
            </div>
          </div>

          {/* Login Card */}
          <div className="bg-white rounded-lg shadow-lg p-8 border border-gray-200">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">Welcome Back</h2>
            <p className="text-xl font-semibold text-gray-900 mb-2">Sign In</p>
            <p className="text-sm text-gray-600 mb-8">Enter your credentials to access your account</p>

            <form onSubmit={handleLogin} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-gray-900 font-medium text-sm">
                Email Address <span className="text-red-500">*</span>
              </Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                  required
                  className="pl-10 h-11 border-gray-300 focus:border-gray-900 focus:ring-gray-900 transition-all duration-300 bg-white"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-gray-900 font-medium text-sm">
                Password <span className="text-red-500">*</span>
              </Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  className="pl-10 pr-10 h-11 border-gray-300 focus:border-gray-900 focus:ring-gray-900 transition-all duration-300 bg-white"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="remember"
                  className="w-4 h-4 text-gray-900 border-gray-300 rounded focus:ring-gray-900"
                />
                <Label htmlFor="remember" className="ml-2 text-sm text-gray-600 cursor-pointer">
                  Remember me
                </Label>
              </div>
              <a href="#" className="text-sm text-gray-600 hover:text-gray-900">
                Forgot password?
              </a>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full h-12 text-base font-semibold bg-gray-900 hover:bg-gray-800 text-white shadow-md transition-all duration-300"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2"></div>
                  Signing In...
                </span>
              ) : (
                <>
                  <LogIn className="mr-2 w-5 h-5" />
                  Sign In
                </>
              )}
            </Button>

            <p className="text-center text-sm text-gray-500 mt-6">
              Don't have an account? Contact your administrator
            </p>
          </form>
          </div>
        </div>
      </div>

      {/* Mobile: Show logo at bottom */}
      <div className="lg:hidden absolute bottom-6 left-6 z-10">
        <div className="w-10 h-10 bg-white flex items-center justify-center">
          <span className="text-black font-bold text-lg">{brand.logo}</span>
        </div>
      </div>

      <style>{`
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fade-in {
          animation: fade-in 0.5s ease-out;
        }
      `}</style>
    </div>
  );
};

export default Login;
