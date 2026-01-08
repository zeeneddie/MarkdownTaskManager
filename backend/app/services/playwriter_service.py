"""
PlaywriterService - Streamlined Browser Automation

Week 78: Single execute tool with 90% less context than Playwright MCP.
Provides tab permission management and convenience methods.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID, uuid4
from dataclasses import dataclass, field

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.browser_automation import (
    PlaywriterSession,
    PlaywriterExecution,
    PlaywriterTab,
    SessionStatus,
    ExecutionStatus,
    BrowserType
)

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of a Playwright code execution."""
    success: bool
    result: Any = None
    error: Optional[str] = None
    screenshot_path: Optional[str] = None
    execution_time_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "screenshot_path": self.screenshot_path,
            "execution_time_ms": self.execution_time_ms
        }


@dataclass
class TabInfo:
    """Information about a browser tab."""
    tab_index: int
    url: Optional[str]
    title: Optional[str]
    permitted: bool
    last_accessed: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tab_index": self.tab_index,
            "url": self.url,
            "title": self.title,
            "permitted": self.permitted,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None
        }


class PlaywriterService:
    """
    Streamlined browser automation service.

    Key Features:
    - Single execute tool (90% less context than Playwright MCP)
    - Tab permission management
    - Convenience methods for common actions
    - Execution history tracking
    """

    # Default browser settings
    DEFAULT_VIEWPORT = {"width": 1280, "height": 720}
    DEFAULT_BROWSER = BrowserType.CHROMIUM

    # Code templates for convenience methods
    CODE_TEMPLATES = {
        "click": "await page.click('{selector}')",
        "type": "await page.type('{selector}', '{text}')",
        "fill": "await page.fill('{selector}', '{value}')",
        "screenshot": "await page.screenshot(path='{path}')",
        "goto": "await page.goto('{url}')",
        "wait_for_selector": "await page.wait_for_selector('{selector}')",
        "get_text": "await page.text_content('{selector}')",
        "get_attribute": "await page.get_attribute('{selector}', '{attribute}')",
        "select": "await page.select_option('{selector}', '{value}')",
        "check": "await page.check('{selector}')",
        "uncheck": "await page.uncheck('{selector}')",
        "press": "await page.press('{selector}', '{key}')",
        "evaluate": "await page.evaluate('{expression}')",
    }

    def __init__(self, db: Session):
        self.db = db
        self._browser = None
        self._context = None
        self._pages: Dict[int, Any] = {}

    async def create_session(
        self,
        name: str,
        description: Optional[str] = None,
        browser_type: str = "chromium",
        headless: bool = True,
        viewport_width: int = 1280,
        viewport_height: int = 720,
        context_options: Optional[Dict[str, Any]] = None
    ) -> PlaywriterSession:
        """Create a new browser automation session."""
        session = PlaywriterSession(
            id=uuid4(),
            name=name,
            description=description,
            browser_type=browser_type,
            headless=headless,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            context_options=context_options or {},
            status=SessionStatus.CREATED.value,
            created_at=datetime.utcnow()
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        logger.info(f"Created playwriter session: {session.id}")
        return session

    async def start_session(self, session_id: UUID) -> Dict[str, Any]:
        """
        Start the browser session.

        Note: In production, this would launch actual Playwright browser.
        For now, we simulate the session start.
        """
        session = self.db.get(PlaywriterSession, session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if session.status == SessionStatus.ACTIVE.value:
            return {"status": "already_active", "session_id": str(session_id)}

        # In production: Launch browser here
        # For now, just update status
        session.status = SessionStatus.ACTIVE.value
        session.started_at = datetime.utcnow()
        self.db.commit()

        # Create initial tab
        initial_tab = PlaywriterTab(
            id=uuid4(),
            session_id=session_id,
            tab_index=0,
            url="about:blank",
            title="New Tab",
            permitted=True,  # Initial tab is auto-permitted
            permitted_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        self.db.add(initial_tab)
        self.db.commit()

        return {
            "status": "started",
            "session_id": str(session_id),
            "browser_type": session.browser_type,
            "headless": session.headless,
            "viewport": {
                "width": session.viewport_width,
                "height": session.viewport_height
            }
        }

    async def close_session(self, session_id: UUID) -> Dict[str, Any]:
        """Close the browser session."""
        session = self.db.get(PlaywriterSession, session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # In production: Close browser here
        session.status = SessionStatus.CLOSED.value
        session.closed_at = datetime.utcnow()
        self.db.commit()

        return {
            "status": "closed",
            "session_id": str(session_id),
            "closed_at": session.closed_at.isoformat()
        }

    async def execute(
        self,
        session_id: UUID,
        code: str,
        tab_id: Optional[int] = None
    ) -> ExecutionResult:
        """
        Execute Playwright code in the session.

        This is the main tool - a single execute command that can run
        any Playwright code, providing 90% context reduction vs full MCP.

        Args:
            session_id: Session ID
            code: Playwright code to execute
            tab_id: Optional tab index to execute in

        Returns:
            ExecutionResult with success/failure and any output
        """
        session = self.db.get(PlaywriterSession, session_id)
        if not session:
            return ExecutionResult(success=False, error=f"Session not found: {session_id}")

        if session.status != SessionStatus.ACTIVE.value:
            return ExecutionResult(success=False, error=f"Session not active: {session.status}")

        # Check tab permission if specified
        if tab_id is not None:
            tab = self.db.execute(
                select(PlaywriterTab).where(
                    PlaywriterTab.session_id == session_id,
                    PlaywriterTab.tab_index == tab_id
                )
            ).scalar_one_or_none()

            if tab and not tab.permitted:
                return ExecutionResult(
                    success=False,
                    error=f"Tab {tab_id} not permitted. Request permission first."
                )

        # Record execution
        execution = PlaywriterExecution(
            id=uuid4(),
            session_id=session_id,
            tab_id=tab_id,
            code=code,
            status=ExecutionStatus.RUNNING.value,
            created_at=datetime.utcnow()
        )
        self.db.add(execution)
        self.db.commit()

        start_time = datetime.utcnow()

        try:
            # In production: Execute actual Playwright code here
            # For now, we simulate execution
            result = await self._simulate_execution(code)

            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            execution.status = ExecutionStatus.COMPLETED.value
            execution.result = result
            execution.execution_time_ms = execution_time
            execution.completed_at = datetime.utcnow()
            self.db.commit()

            return ExecutionResult(
                success=True,
                result=result,
                execution_time_ms=execution_time
            )

        except Exception as e:
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            execution.status = ExecutionStatus.FAILED.value
            execution.error = str(e)
            execution.execution_time_ms = execution_time
            execution.completed_at = datetime.utcnow()
            self.db.commit()

            logger.error(f"Execution failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time
            )

    async def _simulate_execution(self, code: str) -> Dict[str, Any]:
        """
        Simulate Playwright code execution.

        In production, this would use actual Playwright.
        """
        # Parse code to determine action type
        code_lower = code.lower()

        if "goto" in code_lower:
            return {"action": "navigation", "status": "completed"}
        elif "click" in code_lower:
            return {"action": "click", "status": "completed"}
        elif "type" in code_lower or "fill" in code_lower:
            return {"action": "input", "status": "completed"}
        elif "screenshot" in code_lower:
            return {"action": "screenshot", "path": "/tmp/screenshot.png"}
        elif "text_content" in code_lower:
            return {"action": "extract", "text": "Simulated text content"}
        elif "evaluate" in code_lower:
            return {"action": "evaluate", "result": "Simulated JS result"}
        else:
            return {"action": "custom", "status": "completed"}

    # Convenience Methods

    async def click(self, session_id: UUID, selector: str, tab_id: Optional[int] = None) -> ExecutionResult:
        """Click on an element."""
        code = self.CODE_TEMPLATES["click"].format(selector=selector)
        return await self.execute(session_id, code, tab_id)

    async def type_text(
        self,
        session_id: UUID,
        selector: str,
        text: str,
        tab_id: Optional[int] = None
    ) -> ExecutionResult:
        """Type text into an element."""
        code = self.CODE_TEMPLATES["type"].format(selector=selector, text=text)
        return await self.execute(session_id, code, tab_id)

    async def fill(
        self,
        session_id: UUID,
        selector: str,
        value: str,
        tab_id: Optional[int] = None
    ) -> ExecutionResult:
        """Fill a form field."""
        code = self.CODE_TEMPLATES["fill"].format(selector=selector, value=value)
        return await self.execute(session_id, code, tab_id)

    async def screenshot(
        self,
        session_id: UUID,
        path: str = "/tmp/screenshot.png",
        tab_id: Optional[int] = None
    ) -> ExecutionResult:
        """Take a screenshot."""
        code = self.CODE_TEMPLATES["screenshot"].format(path=path)
        result = await self.execute(session_id, code, tab_id)
        if result.success:
            result.screenshot_path = path
        return result

    async def goto(self, session_id: UUID, url: str, tab_id: Optional[int] = None) -> ExecutionResult:
        """Navigate to a URL."""
        code = self.CODE_TEMPLATES["goto"].format(url=url)
        return await self.execute(session_id, code, tab_id)

    async def extract_data(
        self,
        session_id: UUID,
        selector: str,
        tab_id: Optional[int] = None
    ) -> ExecutionResult:
        """Extract text content from elements."""
        code = f"await page.query_selector_all('{selector}').then(els => Promise.all(els.map(e => e.text_content())))"
        return await self.execute(session_id, code, tab_id)

    async def fill_form(
        self,
        session_id: UUID,
        fields: Dict[str, str],
        tab_id: Optional[int] = None
    ) -> ExecutionResult:
        """Fill multiple form fields."""
        code_parts = []
        for selector, value in fields.items():
            code_parts.append(f"await page.fill('{selector}', '{value}')")
        code = "\n".join(code_parts)
        return await self.execute(session_id, code, tab_id)

    # Tab Management

    async def get_tabs(self, session_id: UUID) -> List[TabInfo]:
        """Get all tabs for a session."""
        tabs = self.db.execute(
            select(PlaywriterTab).where(PlaywriterTab.session_id == session_id)
        ).scalars().all()

        return [
            TabInfo(
                tab_index=tab.tab_index,
                url=tab.url,
                title=tab.title,
                permitted=tab.permitted,
                last_accessed=tab.last_accessed
            )
            for tab in tabs
        ]

    async def get_permitted_tabs(self, session_id: UUID) -> List[TabInfo]:
        """Get only permitted tabs."""
        tabs = self.db.execute(
            select(PlaywriterTab).where(
                PlaywriterTab.session_id == session_id,
                PlaywriterTab.permitted == True
            )
        ).scalars().all()

        return [
            TabInfo(
                tab_index=tab.tab_index,
                url=tab.url,
                title=tab.title,
                permitted=True,
                last_accessed=tab.last_accessed
            )
            for tab in tabs
        ]

    async def request_tab_permission(
        self,
        session_id: UUID,
        tab_index: int,
        requested_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Request permission to access a tab.

        In production, this would trigger a human approval flow.
        For now, we auto-approve with a note.
        """
        tab = self.db.execute(
            select(PlaywriterTab).where(
                PlaywriterTab.session_id == session_id,
                PlaywriterTab.tab_index == tab_index
            )
        ).scalar_one_or_none()

        if not tab:
            # Create new tab record
            tab = PlaywriterTab(
                id=uuid4(),
                session_id=session_id,
                tab_index=tab_index,
                permitted=False,
                created_at=datetime.utcnow()
            )
            self.db.add(tab)
            self.db.commit()

        return {
            "status": "pending_approval",
            "tab_index": tab_index,
            "session_id": str(session_id),
            "requested_by": requested_by,
            "message": "Permission request submitted. Awaiting approval."
        }

    async def grant_tab_permission(
        self,
        session_id: UUID,
        tab_index: int,
        granted_by: str = "admin"
    ) -> Dict[str, Any]:
        """Grant permission to access a tab."""
        tab = self.db.execute(
            select(PlaywriterTab).where(
                PlaywriterTab.session_id == session_id,
                PlaywriterTab.tab_index == tab_index
            )
        ).scalar_one_or_none()

        if not tab:
            raise ValueError(f"Tab not found: session={session_id}, index={tab_index}")

        tab.permitted = True
        tab.permitted_at = datetime.utcnow()
        tab.permitted_by = granted_by
        self.db.commit()

        return {
            "status": "granted",
            "tab_index": tab_index,
            "granted_by": granted_by,
            "granted_at": tab.permitted_at.isoformat()
        }

    async def revoke_tab_permission(
        self,
        session_id: UUID,
        tab_index: int
    ) -> Dict[str, Any]:
        """Revoke permission to access a tab."""
        tab = self.db.execute(
            select(PlaywriterTab).where(
                PlaywriterTab.session_id == session_id,
                PlaywriterTab.tab_index == tab_index
            )
        ).scalar_one_or_none()

        if not tab:
            raise ValueError(f"Tab not found: session={session_id}, index={tab_index}")

        tab.permitted = False
        self.db.commit()

        return {
            "status": "revoked",
            "tab_index": tab_index
        }

    # Session Management

    async def get_session(self, session_id: UUID) -> Optional[Dict[str, Any]]:
        """Get session details."""
        session = self.db.get(PlaywriterSession, session_id)
        if not session:
            return None

        tabs = await self.get_tabs(session_id)
        executions = self.db.execute(
            select(PlaywriterExecution)
            .where(PlaywriterExecution.session_id == session_id)
            .order_by(PlaywriterExecution.created_at.desc())
            .limit(10)
        ).scalars().all()

        return {
            "id": str(session.id),
            "name": session.name,
            "description": session.description,
            "browser_type": session.browser_type,
            "headless": session.headless,
            "viewport": {
                "width": session.viewport_width,
                "height": session.viewport_height
            },
            "status": session.status,
            "error_message": session.error_message,
            "tabs": [t.to_dict() for t in tabs],
            "recent_executions": [
                {
                    "id": str(e.id),
                    "code": e.code[:100] + "..." if len(e.code) > 100 else e.code,
                    "status": e.status,
                    "execution_time_ms": e.execution_time_ms,
                    "created_at": e.created_at.isoformat() if e.created_at else None
                }
                for e in executions
            ],
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "closed_at": session.closed_at.isoformat() if session.closed_at else None
        }

    async def list_sessions(
        self,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List browser sessions."""
        query = select(PlaywriterSession)

        if status:
            query = query.where(PlaywriterSession.status == status)

        query = query.order_by(PlaywriterSession.created_at.desc()).limit(limit)

        sessions = self.db.execute(query).scalars().all()

        return [
            {
                "id": str(s.id),
                "name": s.name,
                "browser_type": s.browser_type,
                "status": s.status,
                "created_at": s.created_at.isoformat() if s.created_at else None
            }
            for s in sessions
        ]

    async def get_execution_history(
        self,
        session_id: UUID,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get execution history for a session."""
        executions = self.db.execute(
            select(PlaywriterExecution)
            .where(PlaywriterExecution.session_id == session_id)
            .order_by(PlaywriterExecution.created_at.desc())
            .limit(limit)
        ).scalars().all()

        return [
            {
                "id": str(e.id),
                "tab_id": e.tab_id,
                "code": e.code,
                "result": e.result,
                "error": e.error,
                "status": e.status,
                "execution_time_ms": e.execution_time_ms,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "completed_at": e.completed_at.isoformat() if e.completed_at else None
            }
            for e in executions
        ]
