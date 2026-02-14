// miniprogram/services/assessment.ts
import { request } from './request';

interface StartAssessmentResponse {
  assessment_id: string;
  first_question: any;
}

interface SubmitAnswerRequest {
  assessment_id: string;
  question_id: string;
  answer_index: number;
  time_spent: number;
}

interface SubmitAnswerResponse {
  is_correct: boolean;
  explanation?: string;
  next_question?: any;
}

interface CompleteAssessmentRequest {
  assessment_id: string;
}

interface AssessmentResult {
  overall_level: string;
  ability_score: number;
  confidence: number;
  dimensions: {
    [key: string]: {
      level: string;
      accuracy: number;
      ability: number;
    };
  };
  weak_areas: string[];
  strong_areas: string[];
  recommendations: {
    suggested_scenarios: string[];
    focus_areas: string[];
    estimated_study_days: number;
  };
  duration?: number;
}

class AssessmentService {
  /**
   * 启动评估
   */
  async startAssessment(): Promise<StartAssessmentResponse> {
    return await request.post<StartAssessmentResponse>('/assessment/start', {});
  }

  /**
   * 提交答案
   */
  async submitAnswer(data: SubmitAnswerRequest): Promise<SubmitAnswerResponse> {
    return await request.post<SubmitAnswerResponse>('/assessment/answer', data);
  }

  /**
   * 完成评估
   */
  async completeAssessment(data: CompleteAssessmentRequest): Promise<AssessmentResult> {
    return await request.post<AssessmentResult>('/assessment/complete', data);
  }

  /**
   * 获取评估历史
   */
  async getHistory(): Promise<any[]> {
    const response = await request.get<{ assessments: any[] }>('/assessment/history');
    return response.assessments || [];
  }
}

export const assessmentService = new AssessmentService();
