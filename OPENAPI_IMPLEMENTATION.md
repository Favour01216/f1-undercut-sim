# OpenAPI Documentation and Validation Implementation

This document summarizes the comprehensive OpenAPI documentation and strict request/response validation that has been added to the FastAPI application.

## ✅ Completed Features

### 1. Strict Pydantic Models with Exact Types and Bounds

#### SimIn (Request Model)
```python
class SimIn(BaseModel):
    """Request model for undercut simulation with strict validation."""
    gp: GP_CHOICES = Field(..., description="Grand Prix circuit identifier")
    year: int = Field(..., description="Race year", ge=2020, le=2024)
    driver_a: str = Field(..., description="Driver attempting undercut", min_length=1, max_length=50)
    driver_b: str = Field(..., description="Driver being undercut", min_length=1, max_length=50)
    compound_a: COMPOUND_CHOICES = Field(..., description="Tire compound for driver A")
    lap_now: conint(ge=1, le=100) = Field(..., description="Current lap number")
    samples: conint(ge=1, le=10000) = Field(1000, description="Number of Monte Carlo samples")
```

#### SimOut (Response Model)
```python
class SimOut(BaseModel):
    """Response model for undercut simulation with strict validation."""
    p_undercut: confloat(ge=0, le=1) = Field(..., description="Probability of successful undercut (0-1)")
    pitLoss_s: float = Field(..., description="Expected pit stop time loss in seconds")
    outLapDelta_s: float = Field(..., description="Expected outlap penalty in seconds")
    avgMargin_s: Optional[float] = Field(None, description="Average margin of success/failure in seconds")
    assumptions: Dict[str, Any] = Field(..., description="Model assumptions and parameters used")
```

### 2. Comprehensive Enum Definitions

#### Grand Prix Circuits
```python
GP_CHOICES = Literal[
    "bahrain", "imola", "monza", "monaco", "spain", "canada", "austria", 
    "silverstone", "hungary", "belgium", "netherlands", "italy", "singapore",
    "japan", "qatar", "usa", "mexico", "brazil", "abu_dhabi", "australia",
    "china", "azerbaijan", "miami", "france", "portugal", "russia", "turkey",
    "saudi_arabia", "las_vegas"
]
```

#### Tire Compounds
```python
COMPOUND_CHOICES = Literal["SOFT", "MEDIUM", "HARD"]
```

### 3. Health Endpoint
```python
@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint returning service status."""
    return {"status": "ok"}
```

### 4. Enhanced FastAPI Configuration
```python
app = FastAPI(
    title="F1 Undercut Simulator",
    description="API for F1 undercut simulation and probability analysis with strict validation",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "F1 Undercut Simulator API",
        "email": "favour@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)
```

### 5. Comprehensive Unit Tests

The test suite includes validation tests for:

- **Invalid Grand Prix circuits** - Tests rejection of invalid circuit names
- **Invalid tire compounds** - Tests rejection of non-SOFT/MEDIUM/HARD values
- **Negative lap numbers** - Tests rejection of lap_now < 1
- **Lap numbers too high** - Tests rejection of lap_now > 100
- **Samples too low** - Tests rejection of samples < 1
- **Samples too high** - Tests rejection of samples > 10000
- **Year too low** - Tests rejection of year < 2020
- **Year too high** - Tests rejection of year > 2024
- **Empty driver names** - Tests rejection of empty strings
- **Driver names too long** - Tests rejection of names > 50 characters
- **Valid data acceptance** - Tests that all valid combinations are accepted

### 6. OpenAPI Export Script

Created `scripts/openapi_export.py` with features:
- Exports OpenAPI schema to static JSON file
- Command-line interface with options
- Pretty printing and schema summary
- Error handling and validation
- Build-time integration ready

#### Usage:
```bash
# Basic export
python3 scripts/openapi_export.py

# Custom output path
python3 scripts/openapi_export.py -o docs/openapi.json

# Pretty print with summary
python3 scripts/openapi_export.py --pretty
```

## 🔧 Validation Rules Implemented

### Request Validation (SimIn)
- `gp`: Must be one of 29 valid Grand Prix circuits
- `year`: Integer between 2020 and 2024 (inclusive)
- `driver_a`: String 1-50 characters
- `driver_b`: String 1-50 characters  
- `compound_a`: Must be "SOFT", "MEDIUM", or "HARD"
- `lap_now`: Integer between 1 and 100 (inclusive)
- `samples`: Integer between 1 and 10000 (inclusive), defaults to 1000

### Response Validation (SimOut)
- `p_undercut`: Float between 0.0 and 1.0 (inclusive)
- `pitLoss_s`: Float (no bounds)
- `outLapDelta_s`: Float (no bounds)
- `avgMargin_s`: Optional float (can be None)
- `assumptions`: Dictionary with any string keys and any values

## 📚 OpenAPI Documentation Features

### Automatic Documentation
- **Swagger UI** available at `/docs`
- **ReDoc** available at `/redoc`
- **OpenAPI JSON** available at `/openapi.json`

### Enhanced Schema Information
- Detailed descriptions for all fields
- Type constraints and validation rules
- Example values and format specifications
- Contact and license information
- Comprehensive error response documentation

## 🧪 Testing Strategy

### Unit Tests
- 15+ validation test cases covering all edge cases
- Tests for both valid and invalid data scenarios
- Deterministic result testing
- Integration test markers for CI/CD

### Test Coverage
- ✅ All validation rules tested
- ✅ Error response format verified
- ✅ Success response structure verified
- ✅ Edge case handling confirmed

## 🚀 Build Integration

### OpenAPI Export
The export script can be integrated into build processes:

```bash
# In your build script
python3 scripts/openapi_export.py -o dist/openapi.json

# Or with pretty output for documentation
python3 scripts/openapi_export.py -o docs/api-schema.json --pretty
```

### CI/CD Integration
```yaml
# Example GitHub Actions step
- name: Export OpenAPI Schema
  run: python3 scripts/openapi_export.py -o docs/openapi.json
```

## 📋 API Endpoints

### GET /health
- **Description**: Health check endpoint
- **Response**: `{"status": "ok"}`
- **Status Codes**: 200

### POST /simulate
- **Description**: Simulate undercut probability between two drivers
- **Request Body**: SimIn model
- **Response**: SimOut model
- **Status Codes**: 200 (success), 422 (validation error), 500 (server error)

### GET /
- **Description**: Root endpoint with API information
- **Response**: API metadata and available endpoints

## 🔍 Error Handling

### Validation Errors (422)
- Detailed error messages for each validation failure
- Field-specific error reporting
- Clear indication of what values are acceptable

### Server Errors (500)
- Graceful error handling with descriptive messages
- Logging of errors for debugging
- User-friendly error responses

## 📈 Benefits Achieved

1. **Type Safety**: Strict typing prevents runtime errors
2. **API Documentation**: Auto-generated, comprehensive docs
3. **Client Generation**: OpenAPI schema enables client SDK generation
4. **Validation**: Request/response validation ensures data integrity
5. **Testing**: Comprehensive test coverage ensures reliability
6. **Maintainability**: Clear models and documentation improve code maintainability
7. **Developer Experience**: Clear error messages and documentation improve DX

This implementation provides a production-ready FastAPI application with comprehensive OpenAPI documentation and strict validation as requested.