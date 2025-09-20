# F1 API Client - TypeScript Lead Implementation

## 🎯 Implementation Summary

As a TypeScript lead, I've implemented comprehensive Zod validation for the F1 API client with robust error handling and type safety. Here's what was delivered:

## ✅ Key Features Implemented

### 1. **Comprehensive Zod Schemas**

- **SimulationRequestSchema**: Validates all request parameters with proper constraints
- **SimulationResponseSchema**: Validates API responses with flexible assumptions object
- **BackendStatusSchema**: Validates health check responses
- **HeatmapDataPointSchema**: Validates data visualization points

### 2. **Runtime Type Safety**

```typescript
// Before: Unsafe API calls
const response = await fetch('/simulate', { ... });
const data = await response.json(); // Any unknown data

// After: Validated API calls
const validatedData = SimulationResponseSchema.parse(data); // Throws on invalid data
```

### 3. **Custom Error Types with User-Friendly Messages**

- **ApiValidationError**: For malformed responses from server
- **ApiNetworkError**: For HTTP/network failures
- **User-friendly error messages**: Technical errors converted to actionable user messages

### 4. **Bulletproof API Client**

```typescript
class F1ApiClient {
  // All responses validated through Zod schemas
  private parseResponse<T>(schema: z.ZodSchema<T>, data: unknown): T;

  // Request validation before sending
  async simulate(request: SimulationRequest): Promise<SimulationResponse>;

  // Network error handling
  private async fetchWithValidation<T>(
    url: string,
    schema: z.ZodSchema<T>
  ): Promise<T>;
}
```

## 🛡️ Protection Against Malformed Payloads

### **Request Validation (Client-Side)**

- Invalid GP choices are rejected (`"invalid-gp"` → Error)
- Year range validation (`2025` → Error: "must be at most 2024")
- Compound validation (`"ULTRA_SOFT"` → Error: "must be one of SOFT, MEDIUM, HARD")
- Numeric range validation (`lap_now: 101` → Error: "must be at most 100")

### **Response Validation (Server-Side)**

- Probability bounds (`p_undercut: 1.5` → Error: "must be at most 1")
- Required field validation (missing `pitLoss_s` → Error)
- Type validation (`p_undercut: "75%"` → Error: "expected number, got string")

## 🧪 Comprehensive Testing

### **Manual Validation Test Results**

```bash
npx tsx lib/api-validation-test.ts
```

**Test Results:**

- ✅ Valid requests parsed successfully with defaults applied
- ✅ Invalid GP choices correctly rejected
- ✅ Invalid compounds correctly rejected
- ✅ Future years correctly rejected
- ✅ Response probability bounds enforced
- ✅ User-friendly error messages generated
- ✅ Validation utilities work correctly

### **Key Test Scenarios Covered**

1. **Valid Data**: Ensures proper requests/responses pass validation
2. **Invalid Enums**: GP and compound choices are strictly enforced
3. **Range Validation**: Years, laps, probabilities within bounds
4. **Required Fields**: Missing data is caught and reported
5. **Type Safety**: String/number mismatches are detected
6. **Error Handling**: Different error types generate appropriate messages

## 📊 Error Handling Examples

### **Validation Errors**

```typescript
// Malformed server response
{
  "p_undercut": 1.5,  // Invalid: > 1.0
  "pitLoss_s": 23.5
}
// → "Invalid data type for p_undercut: expected number ≤ 1.0, got 1.5"
```

### **Network Errors**

```typescript
// HTTP 400 Bad Request
// → "Invalid request parameters. Please check your inputs."

// HTTP 500 Internal Server Error
// → "Server error (500). Please try again later."

// Network connection failure
// → "Network error. Please check your connection and try again."
```

### **Request Validation**

```typescript
const result = validateSimulationRequest({
  gp: "invalid-gp",
  year: 2025,
  driver_a: "",
});

// Returns:
{
  isValid: false,
  errors: [
    "gp: must be one of bahrain, saudi-arabia, australia, ...",
    "year: must be at most 2024",
    "driver_a: must be at least 1 characters",
    "driver_b: expected string, got undefined",
    "compound_a: expected 'SOFT' | 'MEDIUM' | 'HARD', got undefined",
    "lap_now: expected number, got undefined"
  ]
}
```

## 🚀 Usage in Components

### **Safe API Calls**

```typescript
import { apiClient, handleApiError } from "@/lib/api";

try {
  // Request is validated before sending
  const result = await apiClient.simulate(request);
  // Response is validated after receiving
  setSimulationResult(result); // Type-safe, validated data
} catch (error) {
  const { message, isUserFriendly } = handleApiError(error);
  if (isUserFriendly) {
    toast.error(message); // Show user-friendly message
  } else {
    console.error("Unexpected error:", error);
    toast.error("An unexpected error occurred. Please try again.");
  }
}
```

### **Type-Safe Form Validation**

```typescript
import { validateSimulationRequest } from "@/lib/api";

const onSubmit = (formData) => {
  const validation = validateSimulationRequest(formData);

  if (!validation.isValid) {
    setFieldErrors(validation.errors); // Show specific field errors
    return;
  }

  // formData is now validated and type-safe
  submitSimulation(validation.data);
};
```

## 📋 Files Modified/Created

### **Core Implementation**

- `frontend/lib/api.ts` - Enhanced with Zod schemas and validation
- `frontend/lib/api-validation-test.ts` - Comprehensive manual tests

### **Testing Infrastructure**

- `frontend/package.json` - Added Vitest testing dependencies
- `frontend/vitest.setup.ts` - Test environment setup

### **Dependencies Added**

- `vitest` - Fast unit test runner
- `@vitest/ui` - Test UI interface
- `jsdom` - DOM environment for tests
- `@testing-library/react` - React testing utilities
- `@testing-library/jest-dom` - Additional DOM matchers

## 🎯 Benefits Achieved

### **For Developers**

- ✅ **Type Safety**: Runtime validation matches TypeScript types
- ✅ **Error Prevention**: Malformed data caught before bugs occur
- ✅ **Developer Experience**: Clear error messages and IDE support
- ✅ **Maintainability**: Centralized validation logic

### **For Users**

- ✅ **Reliability**: Invalid server responses don't crash the app
- ✅ **User Experience**: Friendly error messages instead of technical jargon
- ✅ **Data Integrity**: Only valid simulation data is processed
- ✅ **Graceful Degradation**: Network issues handled smoothly

### **For Production**

- ✅ **Robustness**: API client handles edge cases gracefully
- ✅ **Debugging**: Detailed error information for troubleshooting
- ✅ **Monitoring**: Typed errors can be properly tracked and analyzed
- ✅ **Security**: Input validation prevents injection attacks

## 🔮 Future Enhancements

- **Performance**: Add response caching with Zod validation
- **Monitoring**: Integrate with error tracking (Sentry) for validation failures
- **Documentation**: Generate OpenAPI schemas from Zod schemas
- **Advanced Validation**: Custom Zod transforms for data normalization

---

**🎉 The F1 API client now provides enterprise-grade TypeScript validation with comprehensive error handling and bulletproof protection against malformed payloads!**
